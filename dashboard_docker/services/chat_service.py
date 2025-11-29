from typing import List, Dict, Optional, Tuple
import os
import re
import json

import mysql.connector
from google.genai import types

from .gemini_client import get_gemini_client


GEMINI_MODEL = "gemini-2.5-flash"

# Config DB (peut être overridée par des variables d'environnement Docker)
DB_HOST = os.environ.get("DB_HOST", "db")
DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "rootpassword")
DB_NAME = os.environ.get("DB_NAME", "projet_solarx")


# ============================================================================
#  PROMPT SYSTÈME SPÉCIFIQUE AU PROJET SOLARX
# ============================================================================

SYSTEM_INSTRUCTION = """
Tu es **SolarXBot**, assistant IA spécialisé pour un projet de panneaux solaires
et d’analyse énergétique basé sur la région de Genève.

Ta mission principale est d’aider l’utilisateur à :
- comprendre les données météo et énergétiques affichées dans le tableau de bord SolarX (Dash),
- analyser la pertinence des zones pour l’installation de panneaux solaires,
- interpréter les indicateurs (moyennes, tendances, ratios production/consommation),
- proposer des requêtes SQL adaptées à la base MySQL de SolarX,
- produire des réponses claires, pédagogiques et fiables à partir des résultats SQL.

════════════════════════════════════════════
1. STRUCTURE DE LA BASE DE DONNÉES SOLARX
════════════════════════════════════════════

La base MySQL s’appelle `projet_solarx` et contient notamment les tables suivantes :

1) 2026_solarx_pointsgps
   - idpoint (PK, INT AUTO_INCREMENT)
   - latitude (FLOAT)
   - longitude (FLOAT)
   - adresse (VARCHAR)
   → Représente les points GPS où des mesures météo sont collectées.

2) 2026_solarx_mesures
   - id (PK, INT AUTO_INCREMENT)
   - temperature (VARCHAR, °C)
   - ensoleillement (VARCHAR, secondes)
   - irradiance (VARCHAR, kWh/m²/day)
   - precipitation (VARCHAR, mm)
   - date_collecte (VARCHAR, ex. 'YYYY-MM-DD' ou similaire)
   - idpoint (INT, FK → 2026_solarx_pointsgps.idpoint)
   → Contient les mesures météo / solaires par point GPS et date.

3) 2026_solarx_consommation
   - id_consommation (PK, INT AUTO_INCREMENT)
   - nom_commune (VARCHAR(50))
   - consommation (DECIMAL(10,3))  -- MWh
   - annee (INT)
   - population (INT, optionnel)
   → Données de consommation électrique annuelle par commune.

4) 2026_solarx_zone
   - idzone (PK, INT AUTO_INCREMENT)
   - nom (VARCHAR(50))
   - rayon (INT)  -- rayon en mètres (ou unité précisée dans le projet)
   - origin_latitude (FLOAT)
   - origin_longitude (FLOAT)
   → Zones géographiques (ex. disque autour d’un point de référence).

5) 2026_solarx_appartient
   - idzone (INT, FK → 2026_solarx_zone.idzone)
   - idpoint (INT, FK → 2026_solarx_pointsgps.idpoint)
   → Table de relation indiquant quels points GPS appartiennent à quelle zone.

6) 2026_solarx_panneausolaire
   - id (PK, INT AUTO_INCREMENT)
   - nom, prix, numero_modele, garantie, garantie_puissance, ...
   - caract_electrique_stc, puissance_max, tension_pmax, courant_pmax,
     tension_voc, courant_isc, efficacite_module, tolerance_puissance, ...
   - caract_electrique_noct, temperature, caract_temperature,
     gamme_temperature, coef_temp_pmax, coef_temp_voc, coef_temp_isc, ...
   - tension_max_syst, caract_fusibles_serie, caract_materiel,
     dimension_module, poids, type_cellule, taille_cellule, num_cellule,
     type_verre, epaisseur_verre, type_trame, no_diodes_bypass,
     protection_boite_jonction, type_connecteur, section_cable,
     longeur_cable, PDF
   → Fiche technique des panneaux solaires disponibles (caractéristiques,
     performances, dimensions, etc.).

Remarque importante :
- Dans `2026_solarx_mesures`, les valeurs numériques (temperature, ensoleillement,
  irradiance, precipitation) sont stockées en VARCHAR : pour des calculs ou
  agrégations, il faut utiliser CAST ou CONVERT en DECIMAL/FLOAT dans les requêtes SQL.

════════════════════════════════════════════
2. RÔLE ET COMPORTEMENT GÉNÉRAL
════════════════════════════════════════════

Tu es expert dans :
- énergie solaire photovoltaïque (irradiance, production, rendement, orientation, tilt),
- météorologie appliquée au solaire (ensoleillement, température, précipitations),
- analyse de séries temporelles (tendances mensuelles, saisonnalité, anomalies),
- consommation électrique et dimensionnement des installations solaires,
- analyse géospatiale (points GPS, zones, communes, ratios).

À chaque question :
1. Tu identifies le type de demande :
   - conceptuelle (ex: “c’est quoi l’irradiance ?”),
   - chiffrée (moyenne, max, min, tendance, ratio…),
   - comparaison (entre communes, zones, panneaux…),
   - recommandation (où installer, quel panneau choisir…),
   - interprétation de graphique ou carte du dashboard.

2. Si la question requiert des données chiffrées précises, tu dois proposer
   une requête SQL (lecture seule) pour les récupérer.

3. Tu ne dois jamais inventer de nombres qui ne viennent pas :
   - d’un `sql_result` fourni dans le contexte,
   - ou d’informations explicitement données par l’utilisateur.

════════════════════════════════════════════
3. PROTOCOLE D’UTILISATION DE LA BASE SQL
════════════════════════════════════════════

Tu ne peux pas exécuter directement le SQL, mais tu sais le générer.

A. Quand une requête SQL est nécessaire (valeurs précises, moyennes, ratios, etc.) :
   - tu produis un bloc **distinct** au format suivant :

   ```sql_query
   -- Aim: courte phrase expliquant l’objectif de la requête
   SELECT
       ...
   FROM
       ...
   WHERE
       ...
   GROUP BY
       ...
   ORDER BY
       ...;
   ```

   Règles :
   - uniquement des requêtes de lecture (SELECT) :
     * aucune requête d’écriture : pas de INSERT, UPDATE, DELETE,
       DROP, ALTER, TRUNCATE, CREATE, REPLACE, etc.
   - tu utilises les tables et colonnes réellement présentes
     (voir section “Structure de la base de données SolarX”).
   - pour les champs numériques en VARCHAR (temperature, irradiance, etc.),
     tu les **CAST** en type numérique, par exemple :
       CAST(irradiance AS DECIMAL(10,3)) AS irradiance_num
   - tu privilégies les agrégations classiques (`AVG`, `SUM`, `MIN`, `MAX`, `COUNT`).

   Exemple d’objectifs possibles :
   - moyenne mensuelle d’irradiance pour une zone ou une commune,
   - top N communes par consommation ou par ratio production/consommation,
   - comparaison de températures ou d’ensoleillement entre deux années.

B. IMPORTANT :
   - Quand tu as besoin de données SQL pour répondre, ta toute première réponse
     pour cette question doit contenir UNIQUEMENT un bloc ```sql_query ...``` ,
     sans aucune phrase avant ou après.
   - Quand tu n’as pas besoin de SQL, tu réponds directement à l’utilisateur.

════════════════════════════════════════════
4. PROTOCOLE DE LANGUE
════════════════════════════════════════════

- Tu réponds toujours dans **la même langue que la question** (français, anglais, etc.).
- Si l’utilisateur demande explicitement “réponds en [langue]”, tu utilises cette langue.
- Tu gardes un ton professionnel, pédagogique et concret.

════════════════════════════════════════════
5. STRUCTURE DES RÉPONSES FINALES
════════════════════════════════════════════

Tes réponses finales (après exécution du SQL) doivent :
- commencer par une réponse directe ou un résumé en 1–3 phrases,
- ensuite détailler :
  * l’interprétation des données (issues de `sql_result`),
  * les implications pour le projet (ex: potentiel solaire d’une zone),
  * des recommandations possibles (dimensionnement, choix de panneaux, etc.),
- rester aussi concises que possible sans sacrifier la clarté.

Tu évites de répéter exactement la même information plusieurs fois.

════════════════════════════════════════════
6. DONNÉES MANQUANTES OU NON DISPONIBLES
════════════════════════════════════════════

Si les données nécessaires ne sont pas disponibles dans le `sql_result`
ou le contexte :

- tu le dis clairement (par exemple :
  “Les données disponibles ne permettent pas de répondre précisément à cette question.”),
- tu donnes ensuite une explication générale ou qualitative,
- tu peux suggérer quelles nouvelles données ou requêtes seraient utiles,
  sans inventer de valeurs numériques.

════════════════════════════════════════════
7. RÉSUMÉ OPÉRATIONNEL
════════════════════════════════════════════

1) Tu comprends la question et identifies si elle nécessite une requête SQL.
2) Si oui, tu fournis un bloc `sql_query` (SELECT uniquement) adapté à la base SolarX.
3) Le backend exécute cette requête et renvoie un `sql_result`.
4) Tu utilises ce `sql_result` pour produire une réponse riche et claire.
5) Tu réponds dans la langue de l’utilisateur, de façon structurée et pédagogique.
6) Tu n’inventes jamais de chiffres qui ne viennent pas explicitement de la base
   ou du contexte fourni.
"""


# ============================================================================
#  CONSTRUCTION DES CONTENUS POUR GEMINI
# ============================================================================

def build_contents(
    history: List[Dict[str, str]],
    user_message: str,
    image_part: Optional[types.Part] = None,
) -> list:
    """
    Construit la liste de `types.Content` envoyée à Gemini.
    """
    contents: list[types.Content] = []

    # 1) Prompt système / rôle de SolarXBot
    system_content = types.Content(
        role="user",
        parts=[types.Part(text=SYSTEM_INSTRUCTION)],
    )
    contents.append(system_content)

    # 2) Historique de la conversation
    for msg in history:
        contents.append(
            types.Content(
                role=msg["role"],  # "user" ou "model"
                parts=[types.Part(text=msg["text"])],
            )
        )

    # 3) Nouveau message utilisateur (texte + éventuellement image)
    parts: list[types.Part] = []
    if image_part is not None:
        parts.append(image_part)
    parts.append(types.Part(text=user_message))

    contents.append(types.Content(role="user", parts=parts))

    return contents


# ============================================================================
#  HELPERS SQL
# ============================================================================

def _extract_sql_query(text: str) -> Optional[str]:
    """
    Cherche un bloc ```sql_query ... ``` dans le texte,
    enlève les commentaires, et renvoie la requête SQL.
    """
    if not text:
        return None

    m = re.search(r"```sql_query(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if not m:
        return None

    sql_block = m.group(1)

    # Nettoyage ligne par ligne : on enlève les commentaires et les lignes vides
    cleaned_lines = []
    for line in sql_block.splitlines():
        stripped = line.strip()
        if not stripped:
            continue  # ligne vide
        if stripped.startswith("--"):
            continue  # commentaire
        cleaned_lines.append(line)

    sql_clean = "\n".join(cleaned_lines).strip()

    return sql_clean or None


def _execute_sql_query(query: str):
    """
    Exécute une requête SQL en lecture seule sur la base projet_solarx
    et renvoie (noms_colonnes, lignes).
    """
    if not query:
        raise ValueError("Requête SQL vide.")

    # On ignore les espaces au début
    stripped = query.lstrip()
    first_word = stripped.split(None, 1)[0].lower()

    # On n'autorise que SELECT (et éventuellement WITH pour des CTE)
    if first_word not in ("select", "with"):
        raise ValueError("Requête non autorisée (seuls les SELECT sont exécutés).")

    conn = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
    )
    try:
        cur = conn.cursor()
        cur.execute(query)
        rows = cur.fetchall()
        col_names = [d[0] for d in cur.description]
    finally:
        cur.close()
        conn.close()

    return col_names, rows


def _format_sql_result(col_names, rows, max_rows: int = 50) -> str:
    """
    Formate le résultat SQL en tableau markdown (pour l'envoyer à Gemini).
    """
    if not rows:
        return "Aucune ligne renvoyée."

    header = " | ".join(col_names)
    sep = " | ".join(["---"] * len(col_names))
    lines = [header, sep]

    for r in rows[:max_rows]:
        lines.append(" | ".join(str(v) for v in r))

    if len(rows) > max_rows:
        lines.append(f"... ({len(rows) - max_rows} lignes supplémentaires tronquées)")

    return "\n".join(lines)


# ============================================================================
#  FONCTION PRINCIPALE : APPEL À GEMINI
# ============================================================================

def generate_chat_response(
    history: List[Dict[str, str]],
    user_message: str,
    image_bytes: Optional[bytes] = None,
    mime_type: str = "image/jpeg",
) -> Tuple[str, Optional[Dict]]:
    """
    Renvoie un tuple (answer_text, zone_info).

    - answer_text : texte final pour l'utilisateur
    - zone_info   : dict ou None, par ex.:
        {
          "type": "commune",
          "name": "Meyrin",
          "idpoint": null
        }

    Pipeline :

    Phase 1 : on demande à Gemini s'il a besoin de SQL.
        - soit il répond directement à l'utilisateur (pas de bloc ```sql_query```),
        - soit il renvoie UNIQUEMENT un bloc ```sql_query ...```.

    Phase 2 (si SQL) : on exécute la requête sur MySQL, puis on rappelle Gemini
    avec la question, la requête et le résultat pour qu'il formule la réponse
    finale (sans montrer le SQL à l'utilisateur).

    Phase 3 : on demande à Gemini de transformer la réponse texte en JSON
    { "answer": "...", "zone": {...} } pour identifier une éventuelle commune / zone.
    """
    client = get_gemini_client()

    # Prépare éventuellement la partie image
    image_part: Optional[types.Part] = None
    if image_bytes:
        try:
            image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        except Exception:
            image_part = None

    # ==========================
    # PHASE 1 : PLAN SQL / RÉPONSE
    # ==========================
    contents_phase1 = build_contents(history, user_message, image_part=image_part)

    resp1 = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=contents_phase1,
    )

    text1 = (getattr(resp1, "text", "") or "").strip()

    # On regarde s'il y a un bloc ```sql_query ...```
    sql_query = _extract_sql_query(text1)

    # ----- Cas 1 : pas de SQL → texte direct -----
    if not sql_query:
        answer_text = text1
    else:
        # ----- Cas 2 : il y a un SQL → exécution en back -----
        try:
            col_names, rows = _execute_sql_query(sql_query)
        except Exception as e:
            # En cas d'erreur SQL, on renvoie un message d'erreur simple
            answer_text = f"Erreur lors de l'exécution de la requête SQL générée : {e}"
        else:
            sql_result_table = _format_sql_result(col_names, rows)

            # ==========================
            # PHASE 2 : RÉPONSE FINALE AVEC LES DONNÉES
            # ==========================
            phase2_prompt = f"""
Question utilisateur :
{user_message}

Requête SQL que tu as demandée (déjà exécutée) :
```sql
{sql_query}
```

Résultat de la requête (tableau markdown) :
```sql_result
{sql_result_table}
```

Consigne importante :
- Utilise ces résultats pour répondre à la question de l'utilisateur.
- Ne montre PAS la requête SQL, ni le bloc sql_result, ni le code brut.
- Donne une explication claire, pédagogique et structurée, en gardant le contexte
  du projet SolarX (énergie solaire à Genève).
- Réponds dans la même langue que la question de l'utilisateur.
"""
            contents_phase2 = build_contents(history, phase2_prompt, image_part=image_part)

            resp2 = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=contents_phase2,
            )

            try:
                answer_text = (getattr(resp2, "text", "") or "").strip()
            except Exception:
                if getattr(resp2, "candidates", None):
                    cand = resp2.candidates[0]
                    if getattr(cand, "content", None) and getattr(cand.content, "parts", None):
                        texts = [p.text for p in cand.content.parts if getattr(p, "text", None)]
                        if texts:
                            answer_text = "\n".join(texts)
                        else:
                            answer_text = "[Erreur : réponse texte non disponible depuis Gemini]"
                else:
                    answer_text = "[Erreur : réponse texte non disponible depuis Gemini]"

    # ==========================
    # PHASE 3 : EXTRACTION JSON (answer + zone)
    # ==========================
    zone_info: Optional[Dict] = None

    try:
        json_prompt = f"""
Tu es SolarXBot.

Dernière question de l'utilisateur :
"{user_message}"

Ta réponse textuelle :
\"\"\"{answer_text}\"\"\"

TÂCHE :
- Détecte si la question ou la réponse fait référence à une zone géographique précise :
  * nom de commune (présente dans la table 2026_solarx_consommation.nom_commune),
  * ou point GPS (idpoint ou adresse approximative).
- Produis UNIQUEMENT un JSON valide au format :

{{
  "answer": "<réponse à afficher à l'utilisateur (tu peux légèrement reformuler)>",
  "zone": null OU {{
    "type": "commune" ou "point",
    "name": "<nom de la commune ou adresse>",
    "idpoint": <entier ou null>
  }}
}}

Règles :
- La valeur de "answer" doit être dans la même langue que la question utilisateur.
- Si tu n'es pas sûr de la zone, mets "zone": null.
- Ne mets pas de texte avant ou après le JSON, pas de ``` ni de balises.
"""
        contents_json = build_contents(history, json_prompt, image_part=image_part)

        resp_json = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents_json,
        )

        raw_json = (getattr(resp_json, "text", "") or "").strip()

        # Tenter de parser le JSON proposé
        parsed = json.loads(raw_json)

        # Récupérer answer + zone si présent
        if isinstance(parsed, dict):
            if isinstance(parsed.get("answer"), str) and parsed["answer"].strip():
                answer_text = parsed["answer"].strip()
            zone_candidate = parsed.get("zone")
            if isinstance(zone_candidate, dict):
                # On garde uniquement les clés attendues
                zone_info = {
                    "type": zone_candidate.get("type"),
                    "name": zone_candidate.get("name"),
                    "idpoint": zone_candidate.get("idpoint"),
                }
            else:
                zone_info = None

    except Exception:
        # En cas de problème, on retourne simplement le texte original sans zone
        zone_info = None

    return answer_text, zone_info
