"""
Module d'extraction, analyse et gestion des zones industrielles
avec stockage MySQL et initialisation automatique.

- Genève + Annecy chargées au premier démarrage
- Recherche dynamique NON stockée en BDD
- Nettoyage des NaN pour éviter les erreurs MySQL
"""

import os
import warnings
warnings.filterwarnings('ignore')

import mysql.connector
import pandas as pd
import geopandas as gpd
import osmnx as ox
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split


# ============================================================================
# 🔌 CONNEXION MYSQL
# ============================================================================

def get_connection():
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST", "db"),
        user="root",
        password="rootpassword",
        database="projet_solarx"
    )

def ensure_zones_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS zones_industrielles (
            id INT NOT NULL AUTO_INCREMENT,
            ville VARCHAR(255) NOT NULL,
            name VARCHAR(255) NOT NULL,
            latitude DOUBLE NOT NULL,
            longitude DOUBLE NOT NULL,
            surface_m2 DOUBLE NOT NULL,
            niveau_adaptabilite VARCHAR(50) NOT NULL,
            production_potentielle DOUBLE NOT NULL,
            created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            UNIQUE KEY uniq_zone (ville, latitude, longitude)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
        """
    )
    conn.commit()
    cursor.close()
    conn.close()


# ============================================================================
# 🗺️ EXTRACTION DES ZONES INDUSTRIELLES
# ============================================================================

def extract_industrial_zones(zone="Geneva, Switzerland", radius_km=20):
    """Extraction OSM des zones industrielles autour d'une ville."""
    try:
        print(f"\n🔍 Extraction industrielle : {zone} (rayon {radius_km} km)")

        # 1) géocodage
        location = ox.geocode(zone)

        # 2) extraction OSM dans un rayon
        tags = {"landuse": "industrial"}
        gdf = ox.features_from_point(location, tags=tags, dist=radius_km * 1000)

        if gdf.empty:
            print("⚠️ Aucune zone trouvée.")
            return None

        gdf = gdf.reset_index()

        # Calcul surface
        gdf = gdf.to_crs(epsg=2056)
        gdf["surface_m2"] = gdf.geometry.area
        gdf["centroid_x"] = gdf.geometry.centroid.x
        gdf["centroid_y"] = gdf.geometry.centroid.y

        # Retour GPS
        gdf = gdf.to_crs(epsg=4326)
        gdf["latitude"] = gdf.geometry.centroid.y
        gdf["longitude"] = gdf.geometry.centroid.x

        # ML + production solaire
        gdf = train_ml_model(gdf)
        gdf["production_potentielle_kwh"] = gdf["surface_m2"] * 0.15 * 150

        print(f"   ✅ Extraction faite ({len(gdf)} zones)")
        return gdf

    except Exception as e:
        print(f"❌ ERREUR : {e}")
        return None


# ============================================================================
# 🤖 ENTRAÎNEMENT DU MODELE ML
# ============================================================================

def train_ml_model(gdf):
    median_surface = gdf["surface_m2"].median()

    gdf["label_adapte"] = (
        (gdf["surface_m2"] > median_surface) &
        (gdf["centroid_x"] > gdf["centroid_x"].mean())
    ).astype(int)

    if len(gdf) >= 10:
        X = gdf[["surface_m2", "centroid_x", "centroid_y"]]
        y = gdf["label_adapte"]

        test_size = min(0.3, max(0.1, 3 / len(y)))
        Xtrain, Xtest, ytrain, ytest = train_test_split(X, y, test_size=test_size, random_state=42)

        clf = RandomForestClassifier(
            n_estimators=100, max_depth=10, random_state=42, n_jobs=-1
        )
        clf.fit(Xtrain, ytrain)

        gdf["prediction_adapte"] = clf.predict(X)
        print(f"📊 Précision ML : {clf.score(Xtest, ytest):.2%}")

    else:
        gdf["prediction_adapte"] = (gdf["surface_m2"] > median_surface).astype(int)

    def label(row):
        if row["prediction_adapte"] == 1 and row["surface_m2"] > 10000:
            return "Adaptée"
        elif row["surface_m2"] > 5000:
            return "Moyenne"
        return "Non adaptée"

    gdf["niveau_adaptabilite"] = gdf.apply(label, axis=1)

    return gdf


# ============================================================================
# 🔄 CONVERSION EN DATAFRAME (NETTOYAGE NaN)
# ============================================================================

def get_zones_dataframe(gdf):
    df = pd.DataFrame({
        "name": gdf.get("name", [f"Zone {i+1}" for i in range(len(gdf))]),
        "latitude": gdf["latitude"],
        "longitude": gdf["longitude"],
        "surface_m2": gdf["surface_m2"],
        "niveau_adaptabilite": gdf["niveau_adaptabilite"],
        "production_potentielle": gdf["production_potentielle_kwh"] / 1000
    })

    # 🔥 Nettoyage des NaN pour MySQL
    df["name"] = df["name"].fillna("Zone inconnue")
    df["niveau_adaptabilite"] = df["niveau_adaptabilite"].fillna("Non adaptée")
    df["surface_m2"] = df["surface_m2"].fillna(0)
    df["production_potentielle"] = df["production_potentielle"].fillna(0)

    return df


# ============================================================================
# 💾 SAUVEGARDE EN BASE (SEULEMENT INITIALE)
# ============================================================================

def save_default_zones_to_db(df, ville):
    conn = get_connection()
    cursor = conn.cursor()

    sql = """
        INSERT INTO zones_industrielles
        (ville, name, latitude, longitude, surface_m2, niveau_adaptabilite, production_potentielle)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """

    for _, row in df.iterrows():

        cursor.execute(sql, (
            ville,
            row["name"],
            float(row["latitude"]),
            float(row["longitude"]),
            float(row["surface_m2"]),
            row["niveau_adaptabilite"],
            float(row["production_potentielle"])
        ))

    conn.commit()
    cursor.close()
    conn.close()
    print(f"💾 {len(df)} zones enregistrées pour {ville}")


# ============================================================================
# 📤 CHARGEMENT DES ZONES DEPUIS MYSQL
# ============================================================================

def load_zones_from_db():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM zones_industrielles", conn)
    conn.close()
    return df


# ============================================================================
# 🚀 INITIALISATION : Genève + Annecy
# ============================================================================

def initialize_default_data():
    ensure_zones_table()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM zones_industrielles")
    count = cursor.fetchone()[0]

    if count > 0:
        print("📦 BDD déjà remplie → aucune initialisation.")
        cursor.close()
        conn.close()
        return

    print("⚙️ Lancement de l'initialisation (Genève + Annecy)")

    villes = [
        ("Geneva, Switzerland", 30),
        ("Annecy, France", 30)
    ]

    for ville, radius in villes:
        gdf = extract_industrial_zones(ville, radius_km=radius)
        if gdf is None:
            print(f"⚠️ Aucun résultat pour {ville}")
            continue

        df = get_zones_dataframe(gdf)
        save_default_zones_to_db(df, ville)

    cursor.close()
    conn.close()
    print("🎉 Initialisation terminée.")


# ============================================================================
# 🔍 RECHERCHE DYNAMIQUE (AUCUN STOCKAGE)
# ============================================================================

def search_new_region(region_name, radius_km=20):
    gdf = extract_industrial_zones(region_name, radius_km)
    if gdf is None:
        return None

    df = get_zones_dataframe(gdf)
    df["ville"] = region_name
    return df

# # import os
# # import json
# # import warnings
# # warnings.filterwarnings('ignore')

# # import osmnx as ox
# # import geopandas as gpd
# # import pandas as pd
# # import numpy as np
# # from sklearn.ensemble import RandomForestClassifier
# # from sklearn.model_selection import train_test_split
# import mysql.connector
# import os
# import pandas as pd
# import geopandas as gpd
# import osmnx as ox
# import numpy as np
# from sklearn.ensemble import RandomForestClassifier
# from sklearn.model_selection import train_test_split
# import warnings
# warnings.filterwarnings("ignore")

# def get_connection():
#     return mysql.connector.connect(
#         host=os.environ.get("DB_HOST", "db"),
#         user="root",
#         password="rootpassword",
#         database="projet_solarx"
#     )
# def get_zones_dataframe(gdf):
#     return pd.DataFrame({
#         'latitude': gdf['latitude'],
#         'longitude': gdf['longitude'],
#         'surface_m2': gdf['surface_m2'],
#         'niveau_adaptabilite': gdf['niveau_adaptabilite'],
#         'production_potentielle': gdf['production_potentielle_kwh'] / 1000,
#         'name': gdf.get('name', [f'Zone {i+1}' for i in range(len(gdf))])
#     })

# def save_default_zones_to_db(df, ville):
#     conn = get_connection()
#     cursor = conn.cursor()

#     sql = """
#         INSERT INTO zones_industrielles
#         (ville, name, latitude, longitude, surface_m2, niveau_adaptabilite, production_potentielle)
#         VALUES (%s,%s,%s,%s,%s,%s,%s)
#     """

#     for _, row in df.iterrows():
#         cursor.execute(sql, (
#             ville,
#             row["name"],
#             row["latitude"],
#             row["longitude"],
#             float(row["surface_m2"]),
#             row["niveau_adaptabilite"],
#             float(row["production_potentielle"])
#         ))

#     conn.commit()
#     cursor.close()
#     conn.close()
# def load_zones_from_db():
#     conn = get_connection()
#     query = "SELECT * FROM zones_industrielles"
#     df = pd.read_sql(query, conn)
#     conn.close()
#     return df

# def initialize_default_data():
#     conn = get_connection()
#     cursor = conn.cursor()

#     cursor.execute("SELECT COUNT(*) FROM zones_industrielles")
#     count = cursor.fetchone()[0]

#     if count > 0:
#         print("📦 BDD déjà remplie → Aucun chargement initial.")
#         cursor.close()
#         conn.close()
#         return

#     print("⚙️ Initialisation : extraction Genève + Annecy...")

#     villes_initiales = [
#         ("Geneva, Switzerland", 30),
#         ("Annecy, France", 30)
#     ]

#     for ville, radius in villes_initiales:
#         print(f"\n🔍 Extraction : {ville} (rayon {radius} km)")
#         gdf = extract_industrial_zones(ville, radius_km=radius)

#         if gdf is None:
#             print(f"⚠️ Aucune donnée trouvée pour {ville}")
#             continue

#         df = get_zones_dataframe(gdf)
#         df["ville"] = ville

#         save_default_zones_to_db(df, ville)
#         print(f"✅ Données enregistrées pour {ville}")

#     cursor.close()
#     conn.close()
#     print("🎉 Initialisation terminée")



# # =====================================================
# # FONCTION PRINCIPALE D'INITIALISATION
# # =====================================================
# # def initialize_default_data():
# #     """
# #     Initialise automatiquement les données au démarrage du dashboard.
# #     Si le fichier JSON n'existe pas, il est créé pour Genève + communes voisines.
# #     """
# #     json_path = "assets/maps/zones_industrielles.json"
# #     if not os.path.exists(json_path):
# #         print("⚙️ Initialisation : génération des données pour Genève + environs...")
# #         # CHANGEMENT ICI : rayon de 20km pour inclure les communes voisines
# #         df = extract_industrial_zones("Geneva, Switzerland", radius_km=20)
# #         if df is not None:
# #             df = get_zones_dataframe(df)
# #             df["ville"] = "Geneva, Switzerland"
# #             os.makedirs("assets/maps", exist_ok=True)
# #             df.to_json(json_path, orient="records", force_ascii=False)
# #             print("✅ Données initiales créées pour Genève + environs.")
# #         else:
# #             print("⚠️ Impossible de générer les données initiales.")
# #     else:
# #         print("✅ Données industrielles déjà présentes.")

# from database import get_connection

# def initialize_default_data():
#     conn = get_connection()
#     cursor = conn.cursor()

#     # Vérifier si la BDD contient déjà des données
#     cursor.execute("SELECT COUNT(*) FROM zones_industrielles")
#     count = cursor.fetchone()[0]

#     if count > 0:
#         print("📦 BDD déjà remplie → Aucun chargement initial.")
#         cursor.close()
#         conn.close()
#         return

#     print("⚙️ Initialisation : génération des données par défaut (Genève + Annecy)")

#     villes_initiales = [
#         "Geneva, Switzerland",
#         "Annecy, France"
#     ]

#     for ville in villes_initiales:
#         print(f"\n🔍 Extraction des zones pour {ville} (rayon 30 km)...")
#         gdf = extract_industrial_zones(ville, radius_km=30)

#         if gdf is not None:
#             df = get_zones_dataframe(gdf)
#             df["ville"] = ville
#             save_default_zones_to_db(df)   # Enregistrement en BDD uniquement à l'initialisation
#             print(f"✅ Données enregistrées pour {ville}")
#         else:
#             print(f"⚠️ Aucune donnée trouvée pour {ville}")

#     cursor.close()
#     conn.close()
#     print("\n🎉 Initialisation BDD terminée !")



# # =====================================================
# # EXTRACTION DES ZONES INDUSTRIELLES - VERSION RAYON
# # =====================================================
# def extract_industrial_zones(zone="Geneva, Switzerland", radius_km=20, use_cache=True):
#     """
#     Extrait les zones industrielles dans un RAYON autour de la ville.
    
#     CHANGEMENT PRINCIPAL : Au lieu de chercher QUE dans la ville,
#     on cherche dans un rayon de X km autour du centre de la ville.
    
#     Args:
#         zone: Nom de la ville
#         radius_km: Rayon en km (20km = toute l'agglomération genevoise)
#     """
#     try:
#         print(f"🔍 Extraction des zones industrielles pour {zone}...")
#         print(f"   📍 Recherche dans un rayon de {radius_km} km (inclut les communes voisines)")
        
#         # ÉTAPE 1 : Trouver le centre de la ville
#         location = ox.geocode(zone)  # Retourne (latitude, longitude)
#         print(f"   🎯 Centre trouvé : {location[0]:.4f}, {location[1]:.4f}")
        
#         # ÉTAPE 2 : Chercher dans un RAYON autour du centre (pas juste dans la ville)
#         tags = {"landuse": "industrial"}
#         gdf = ox.features_from_point(
#             location,                    # Point central
#             tags=tags,                   # Ce qu'on cherche
#             dist=radius_km * 1000        # Distance en MÈTRES (20km = 20000m)
#         )

#         if gdf.empty:
#             print("⚠️ Aucune zone industrielle trouvée.")
#             return None

#         print(f"   ✅ {len(gdf)} zones trouvées (Geneva + Vernier + Meyrin + Carouge + etc.)")

#         # ÉTAPE 3 : Calcul des surfaces et coordonnées
#         gdf = gdf.reset_index()
#         gdf = gdf.to_crs(epsg=2056)  # Projection suisse pour calcul surface
#         gdf["surface_m2"] = gdf.geometry.area
#         gdf["centroid_x"] = gdf.geometry.centroid.x
#         gdf["centroid_y"] = gdf.geometry.centroid.y

#         gdf = gdf.to_crs(epsg=4326)  # Retour en GPS
#         gdf["latitude"] = gdf.geometry.centroid.y
#         gdf["longitude"] = gdf.geometry.centroid.x

#         # ÉTAPE 4 : Modèle ML et production
#         gdf = train_adaptability_model(gdf)
#         gdf["production_potentielle_kwh"] = gdf["surface_m2"] * 0.15 * 150

#         print(f"✅ {len(gdf)} zones trouvées dans {radius_km}km autour de {zone}.")
#         return gdf

#     except Exception as e:
#         print(f"❌ Erreur lors de l'extraction : {e}")
#         return None


# # =====================================================
# # ENTRAÎNEMENT DU MODÈLE ML
# # =====================================================
# def train_adaptability_model(gdf):
#     surface_thr = gdf["surface_m2"].median()
#     gdf["label_adapte"] = (
#         (gdf["surface_m2"] > surface_thr) &
#         (gdf["centroid_x"] > gdf["centroid_x"].mean())
#     ).astype(int)

#     if len(gdf) >= 10:
#         features = gdf[["surface_m2", "centroid_x", "centroid_y"]].values
#         labels = gdf["label_adapte"].values
#         test_size = min(0.3, max(0.1, 3 / len(labels)))

#         clf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
#         X_train, X_test, y_train, y_test = train_test_split(features, labels, test_size=test_size, random_state=42)
#         clf.fit(X_train, y_train)
#         gdf["prediction_adapte"] = clf.predict(features)
#         print(f"📊 Précision du modèle : {clf.score(X_test, y_test):.2%}")
#     else:
#         gdf["prediction_adapte"] = (gdf["surface_m2"] > gdf["surface_m2"].median()).astype(int)
#         print("⚠️ Peu de données, classification simplifiée.")

#     seuil_bas, seuil_haut = 5000, 10000
#     def categorize(row):
#         if row["prediction_adapte"] == 1 and row["surface_m2"] > seuil_haut:
#             return "Adaptée"
#         elif seuil_bas <= row["surface_m2"] < seuil_haut:
#             return "Moyenne"
#         else:
#             return "Non adaptée"

#     gdf["niveau_adaptabilite"] = gdf.apply(categorize, axis=1)
#     return gdf


# # =====================================================
# # CONVERSION POUR DASH / JSON
# # =====================================================
# def get_zones_dataframe(gdf):
#     return pd.DataFrame({
#         'latitude': gdf['latitude'],
#         'longitude': gdf['longitude'],
#         'surface_m2': gdf['surface_m2'],
#         'niveau_adaptabilite': gdf['niveau_adaptabilite'],
#         'production_potentielle': gdf['production_potentielle_kwh'] / 1000,
#         'name': gdf.get('name', [f'Zone {i+1}' for i in range(len(gdf))])
#     })


# # =====================================================
# # RECHERCHE DYNAMIQUE DE NOUVELLE RÉGION
# # =====================================================
# def search_new_region(region_name, radius_km=20):
#     """
#     Recherche et exporte les zones d'une nouvelle région + ses environs.
    
#     Args:
#         region_name: Nom de la ville
#         radius_km: Rayon de recherche (défaut 20km)
#     """
#     print(f"\n🔎 Recherche et extraction pour {region_name} + {radius_km}km autour...")
#     df = extract_industrial_zones(region_name, radius_km=radius_km)
#     if df is not None:
#         df = get_zones_dataframe(df)
#         df["ville"] = region_name
#         os.makedirs("assets/maps", exist_ok=True)
#         df.to_json("assets/maps/zones_industrielles.json", orient="records", force_ascii=False)
#         print(f"✅ Données mises à jour pour {region_name} + environs")
#     else:
#         print("⚠️ Aucune donnée trouvée pour cette région.")
