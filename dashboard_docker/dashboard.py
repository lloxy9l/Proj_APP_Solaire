import json
import os
import dash
from dash import html, dcc, Input, Output, State, no_update
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import mysql.connector
import pandas as pd
from chatbot_page import get_chatbot_layout, register_chatbot_callbacks
from layouts.home import render_main_content
from layouts.ensoleillement import render_ensoleillement
from layouts.temperature import render_temperature
from layouts.precipitations import render_precipitations
from layouts.optimisation import render_optimisation
from layouts.electricite import render_electricite


from dash import callback_context

from layouts.ia_zones import initialize_default_data, search_new_region, extract_industrial_zones, get_zones_dataframe 
from layouts.industriel import render_zones_industrielles
from layouts.ia_prediction import predict_future_production



initialize_default_data()
zones_df = pd.read_json("assets/maps/zones_industrielles.json")
print(f"✅ {len(zones_df)} zones industrielles chargées (fichier JSON)")

# =====================================================
host = os.environ.get("DB_HOST", "mysql_db")  # Allows deployment to override DB host/IP
node_host = os.environ.get("NODE_HOST", "nodejs")
node_port = os.environ.get("NODE_PORT", "3000")
node_base_url = f"http://{node_host}:{node_port}"
user = "root"
password = "rootpassword"
database = "projet_solarx"

with open('assets/maps/map_precipitation.html', 'r') as file:
    map_precipitation = file.read().replace("http://localhost:3000", node_base_url)

with open('assets/maps/map_ensoleillement.html', 'r') as file:
    map_ensoleillement = file.read().replace("http://localhost:3000", node_base_url)

with open('assets/maps/map_temperature.html', 'r') as file:
    map_temperature = file.read().replace("http://localhost:3000", node_base_url)

with open('assets/maps/map_production.html', 'r') as file:
    map_production = file.read().replace("http://localhost:3000", node_base_url)

with open('assets/maps/map_zones_industrielles.html', 'r') as file:
    map_zones_industrielles = file.read().replace("http://localhost:3000", node_base_url)


##########################################################################################################################################
##########################################################################################################################################
######################              Recuperation données bdd pour carte meteo                            #################################
##########################################################################################################################################
##########################################################################################################################################
def fetch_data():
    conn = mysql.connector.connect(host=host, user=user, password=password, database=database, charset="utf8")
    with conn.cursor(dictionary=True,buffered=True) as c:
        c.execute("""
            SELECT p.latitude, p.longitude, m.temperature, m.ensoleillement, m.irradiance, m.precipitation, m.date_collecte, m.idpoint 
            FROM 2026_solarx_pointsgps p
            JOIN 2026_solarx_mesures m ON p.idpoint = m.idpoint;
        """)
        data = c.fetchall()
        c.execute("""
            SELECT p.adresse, p.idpoint
            FROM 2026_solarx_pointsgps p;
        """)
        data_point = c.fetchall()
        c.execute("SELECT nom_commune, consommation FROM `2026_solarx_consommation` WHERE annee = 2023;")
        data_conso = c.fetchall()
    conn.close()
    
    df = pd.DataFrame(data)
    df["date_collecte"] = pd.to_datetime(df["date_collecte"])
    df[["temperature", "irradiance", "precipitation", "ensoleillement"]] = df[["temperature", "irradiance", "precipitation", "ensoleillement"]].apply(pd.to_numeric, errors='coerce')
    df["ensoleillement"] = df["ensoleillement"]/3600
    df["production"] = df["irradiance"] * 365 * 3

    conso_df = pd.DataFrame(data_conso)
    conso_df["consommation"] = pd.to_numeric(conso_df["consommation"], errors='coerce')

    print("Data collected")
    return df, conso_df, data_point




df, df_conso, data_point = fetch_data()
df = predict_future_production(df)
##########################################################################################################################################
##########################################################################################################################################
######################              Conversion des données en DF pour les utiliser                       #################################
##########################################################################################################################################
##########################################################################################################################################
# Charger les données
data_meteo,data_conso,data_commune = fetch_data()

df_meteo = pd.DataFrame(data_meteo)
# Copie principale utilisée pour les différents graphiques
df = df_meteo.copy()
df_conso = pd.DataFrame(data_conso)
prod_df = df_meteo.copy()
commune_df = pd.DataFrame(data_commune)


# Calculer la moyenne des valeurs pour chaque point GPS
mean_data = df.groupby(["latitude", "longitude"]).mean().reset_index()
global_means = {
    "temperature": df["temperature"].mean(),
    "ensoleillement": df["ensoleillement"].mean(),
    "irradiance": df["irradiance"].mean(),
    "precipitation": df["precipitation"].mean(),
    "consommation":df_conso["consommation"].mean()/1000,
}

#Données pour les lines charts
datalinechart=df
# Extract year and month for grouping
datalinechart['year_month'] = datalinechart['date_collecte'].dt.to_period('M')

# Calculate monthly averages
monthly_datalinechart = datalinechart.groupby('year_month').mean()

# Calculate monthly averages across all years
monthly_data = df.groupby('year_month').mean()

#Données pour la distribution
# Extraire le mois et l'année
df["mois"] = df["date_collecte"].dt.month  # Extraire uniquement le mois (1-12)
# Grouper par mois et calculer la moyenne globale de chaque paramètre (ensoleillement, température, précipitation)
df_mois = df.groupby("mois")[["ensoleillement", "temperature", "precipitation"]].agg({
    "ensoleillement": "mean",  # Moyenne de l'ensoleillement
    "temperature": "mean",    # Moyenne de la température
    "precipitation": "mean"   # Moyenne des précipitations
}).reset_index()

print('Data Fetched')

# =====================================================================
#       OPTIMISATION : score global par point GPS pour panneaux PV
# =====================================================================

# On repart des données météo complètes (une ligne par date et par idpoint)
opt_df = df_meteo.copy()

# Agrégation : moyennes globales par point GPS
opt_points = (
    opt_df.groupby("idpoint")
    .agg(
        latitude=("latitude", "first"),
        longitude=("longitude", "first"),
        temperature=("temperature", "mean"),
        ensoleillement=("ensoleillement", "mean"),
        irradiance=("irradiance", "mean"),
        precipitation=("precipitation", "mean"),
        production=("production", "mean"),
    )
    .reset_index()
)

# Ajout de l'adresse si disponible
if "idpoint" in commune_df.columns:
    opt_points = opt_points.merge(
        commune_df[["idpoint", "adresse"]],
        on="idpoint",
        how="left",
    )

# Petite fonction de normalisation [0,1]
def _normalize(series):
    min_val = series.min()
    max_val = series.max()
    if pd.isna(min_val) or pd.isna(max_val) or max_val == min_val:
        # Si pas de variance ou valeurs manquantes, on renvoie 0.5 (neutre)
        return pd.Series(0.5, index=series.index)
    return (series - min_val) / (max_val - min_val)

# Normalisation des indicateurs
opt_points["norm_ens"] = _normalize(opt_points["ensoleillement"])
opt_points["norm_irr"] = _normalize(opt_points["irradiance"])
opt_points["norm_prod"] = _normalize(opt_points["production"])
opt_points["norm_prec"] = _normalize(opt_points["precipitation"])

# Température : on favorise la proximité d'une température "idéale" (≈20°C)
temp_dev = (opt_points["temperature"] - 20).abs()
opt_points["norm_temp_dev"] = _normalize(temp_dev)

# Scores partiels [0,1] (on inverse pour précipitation & écart de température)
opt_points["score_ens"] = opt_points["norm_ens"]
opt_points["score_irr"] = opt_points["norm_irr"]
opt_points["score_prod"] = opt_points["norm_prod"]
opt_points["score_prec"] = 1 - opt_points["norm_prec"]      # moins de pluie = mieux
opt_points["score_temp"] = 1 - opt_points["norm_temp_dev"]  # proche de 20°C = mieux

for col in ["score_ens", "score_irr", "score_prod", "score_prec", "score_temp"]:
    opt_points[col] = opt_points[col].clip(0, 1)

# Pondérations (ajustables facilement)
w_ens = 0.30
w_irr = 0.25
w_prod = 0.25
w_prec = 0.10
w_temp = 0.10

opt_points["score_global"] = 100 * (
    w_ens * opt_points["score_ens"]
    + w_irr * opt_points["score_irr"]
    + w_prod * opt_points["score_prod"]
    + w_prec * opt_points["score_prec"]
    + w_temp * opt_points["score_temp"]
)

opt_points["score_global"] = opt_points["score_global"].fillna(0.0)

# Tri pour récupérer les meilleurs emplacements
opt_points_sorted = opt_points.sort_values("score_global", ascending=False).reset_index(drop=True)
top_opt_points = opt_points_sorted.head(10)

print("Scores d'optimalité calculés pour", len(opt_points_sorted), "points GPS.")

##########################################################################################################################################
##########################################################################################################################################
######################              Récuperation données bdd pour conso elec carte                       #################################
##########################################################################################################################################
##########################################################################################################################################
def get_data():
    conn = mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database
    )
    
    # Requête SQL pour récupérer la consommation des communes
    query = """
    SELECT nom_commune, consommation, annee
    FROM 2026_solarx_consommation
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# Charger le fichier GeoJSON contenant les polygones des communes
def load_geojson(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        geojson_data = json.load(file)
    return geojson_data

def get_communes_data(df, geojson_data):
    """
    Associe les communes dans le DataFrame aux features du GeoJSON.
    :param df: DataFrame contenant les données des communes (doit contenir une colonne "nom_commune")
    :param geojson_data: Données GeoJSON contenant les polygones des communes
    :return: Liste des features GeoJSON correspondant aux communes dans le DataFrame
    """
    communes_df = df['nom_commune'].unique()
    communes_geo_data = []
    for feature in geojson_data['features']:
        # Vérifier si la clé 'name' existe avant de l'utiliser
        if 'name' in feature['properties'] and feature['properties']['name'] in communes_df:
            communes_geo_data.append(feature)
    return communes_geo_data

# Chargement du fichier GeoJSON et des données communes
geojson_data = load_geojson('geo_data_boundaries.geojson')
df = get_data()

# ==== Pré-calcul des centroïdes des communes depuis le GeoJSON ====

def _compute_centroid_from_geometry(geometry):
    """
    Calcule un centroïde simple (moyenne des points) pour un Polygon ou MultiPolygon.
    Suffisant pour recadrer la carte.
    """
    gtype = geometry.get("type")
    coords = geometry.get("coordinates", [])

    points = []

    if gtype == "Polygon":
        # coords = [ [ [lon, lat], [lon, lat], ... ] ]  (on prend l'anneau extérieur)
        if coords:
            points = coords[0]
    elif gtype == "MultiPolygon":
        # coords = [ [ [ [lon, lat], ... ] ], [ [lon, lat], ... ], ... ]
        for poly in coords:
            if poly:
                points.extend(poly[0])

    if not points:
        return None, None

    lons = [p[0] for p in points]
    lats = [p[1] for p in points]
    return sum(lats) / len(lats), sum(lons) / len(lons)


# Dictionnaire global : nom_commune_normalisé -> {lat, lon}
COMMUNE_CENTROIDS = {}

for feature in geojson_data.get("features", []):
    props = feature.get("properties", {})
    name = props.get("name")
    geometry = feature.get("geometry")

    if not name or not geometry:
        continue

    lat, lon = _compute_centroid_from_geometry(geometry)
    if lat is None or lon is None:
        continue

    key = name.strip().lower()
    COMMUNE_CENTROIDS[key] = {"lat": lat, "lon": lon}

print(f"Centroïdes calculés pour {len(COMMUNE_CENTROIDS)} communes.")


# Étape 1 : Calculer la moyenne globale
moyenne_globale_conso = df['consommation'].mean()
print(f"Moyenne consommation globale (kWh): {moyenne_globale_conso:.2f}")

# Étape 2 : Identifier les communes du GeoJSON
geojson_communes = set(
    feature['properties']['name'].strip().lower()
    for feature in geojson_data['features']
    if 'name' in feature['properties'] and feature['properties']['name']  # pour éviter les None ou vide
)


# Communes déjà présentes dans la BDD
communes_bdd = set(df['nom_commune'].str.strip().str.lower())

# Étape 3 : Détecter les communes manquantes
communes_manquantes = geojson_communes - communes_bdd
print(f"Communes sans consommation : {communes_manquantes}")

# Étape 4 : Créer un DataFrame avec consommation = moyenne
import pandas as pd

communes_manquantes_df = pd.DataFrame({
    'nom_commune': [commune.capitalize() for commune in communes_manquantes],
    'consommation': moyenne_globale_conso,
    'annee': 2023
})

# Fusionner les nouvelles communes avec celles de la BDD
df = pd.concat([df, communes_manquantes_df], ignore_index=True)

# Étape 5 : Mise à jour SQL (ajout des communes manquantes dans la BDD)
import mysql.connector

conn = mysql.connector.connect(
    host=host,
    user="root",
    password="rootpassword",
    database="projet_solarx"
)
cursor = conn.cursor()

# Ajouter les communes manquantes à la BDD
for _, row in communes_manquantes_df.iterrows():
    cursor.execute("""
        INSERT INTO 2026_solarx_consommation (nom_commune, consommation, annee)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE consommation = VALUES(consommation)
    """, (row['nom_commune'], row['consommation'], row['annee']))

conn.commit()
cursor.close()
conn.close()
print(" Données manquantes ajoutées avec la moyenne globale.")


communes_geo_data = get_communes_data(df, geojson_data)
print("Data communed fetched")

##########################################################################################################################################
##########################################################################################################################################
######################              Récuperation données bdd pour carte ratio                            #################################
##########################################################################################################################################
##########################################################################################################################################

def extract_commune(commune_df, df_villes_conso):
    # Conversion des noms de communes en un ensemble pour des comparaisons rapides
    commune_names = set(df_villes_conso["nom_commune"].str.strip().str.lower())
    commune_to_points = {}

    if "adresse" in commune_df.columns:
        for _, row in commune_df.iterrows():
            adresse = row["adresse"]
            idpoint = row["idpoint"]
            # Pour chaque ville dans l'adresse
            for ville in adresse.split(','):
                ville = ville.strip().lower()
                if ville in commune_names:
                    # Ajouter idpoint à la liste associée à la ville
                    if ville not in commune_to_points:
                        commune_to_points[ville] = []
                    commune_to_points[ville].append(idpoint)
                    break
    else:
        print("Colonne 'adresse' introuvable dans le DataFrame.")

    # Convertir le dictionnaire en liste comme souhaité
    return [[ville, points] for ville, points in commune_to_points.items()]


def calculer_ratio(prod_df, conso_df, commune_df):
    communes_en_commun = extract_commune(commune_df, conso_df)
    ratio_dict = {}
    for commune, idpoints in communes_en_commun:
        # Assurez-vous que les noms sont normalisés avant la comparaison
        commune_normalized = commune.lower().strip()
        
        # Normalisation des noms pour la recherche dans le DataFrame
        consommation_moyenne = conso_df[
            conso_df['nom_commune'].str.lower().str.strip() == commune_normalized
        ]['consommation'].mean()
        
        production_moyenne = prod_df[
            prod_df['idpoint'].isin(idpoints)
        ]['production'].mean()
        
        
        if consommation_moyenne > 0 and production_moyenne > 0:
            ratio_dict[commune_normalized] = production_moyenne / consommation_moyenne
    
    return ratio_dict
# Calculer le ratio
ratio_dict = calculer_ratio(prod_df, df_conso, commune_df)

print("Ratios calculés :", ratio_dict)

# Extraire les noms des communes depuis geojson_data
commune_names_geojson = [ft['properties'].get('name', 'Inconnu').lower().strip() for ft in geojson_data['features']]

# Filtrer les communes et leurs ratios
filtered_commune_names = []
filtered_ratio_values = []

for commune, ratio in ratio_dict.items():
    commune_lower = commune.lower().strip()
    if ratio > 0 and commune_lower in commune_names_geojson:
        filtered_commune_names.append(commune.capitalize())
        filtered_ratio_values.append(ratio)

# Vérification de la cohérence des données
if len(filtered_commune_names) != len(filtered_ratio_values):
    print("Erreur : les noms des communes et les valeurs des ratios ne correspondent pas !")

# Création de la carte
filtered_features = [
    feature for feature in geojson_data['features']
    if feature['properties'].get('name', '').lower().strip() in [name.lower().strip() for name in filtered_commune_names]
]




# Initialisation de l'application Dash
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True  # important avec les layouts externes
)
server=app.server

@server.route("/updateRegion", methods=["POST"])
def update_region():
    """Met à jour les zones industrielles selon la région demandée."""
    data = request.json
    region = data.get("region")
    if not region:
        return jsonify({"status": "error", "message": "Aucune région fournie"}), 400
    search_new_region(region)
    return jsonify({"status": "ok", "message": f"Carte mise à jour pour {region}"}), 200


# Style général pour la barre latérale
vertical_header_style = {
    "height": "100vh",  # Prend toute la hauteur de l'écran
    "width": "80px",  # Largeur par défaut du header
    "background-color": "#005dff",  # Couleur de fond
    "color": "white",  # Couleur du texte
    "display": "flex",  # Flexbox pour l'alignement
    "flex-direction": "column",  # Alignement vertical
    "justify-content": "space-between",  # Espacement entre les sections
    "padding": "10px",
    "border-radius": "0 2em 2em 0",
    "transition": "width 0.3s ease",  # Animation pour le changement de largeur
    "overflow": "hidden",  # Masque le contenu qui dépasse
    "position":"fixed",
    "z-index":"100"
}

##########################################################################################################################################
##########################################################################################################################################
######################              HTML conteneur vertical                                              #################################
##########################################################################################################################################
##########################################################################################################################################
vertical_header = html.Div(
    id="vertical-header",  # ID pour appliquer le style CSS au hover
    style=vertical_header_style,
    children=[
        # Logo ou titre
        html.Div(
            children=[
                html.Img(
                    src="assets/img/logo.png",
                    style={"width": "60px", "border-radius": "8px", "margin-top": "10px"},
                ),
            ]
        ),
        # Menu de navigation
        html.Div(
            id="nav-menu", # Ajout d'un ID pour manipuler les enfants dans le callback
            style={
                "display": "flex",
                "flex-direction": "column",  # Utilisation de flexbox pour aligner horizontalement
                "align-items": "flex-left",  # Alignement vertical au centre
                "white-space": "nowrap",  # Empêcher les retours à la ligne
            },
            children=[
                html.A(
                    children=[
                        html.Img(
                            src="assets/img/home.png",  # Icône pour Accueil
                            style={"width": "40px", "margin": "20px 10px", "vertical-align": "middle"},
                        ),
                        html.Span("Accueil", style={"margin-left": "10px", "font-size": "14px", "vertical-align": "middle", "display": "none"}),  # Span pour le texte
                    ],
                    href="/home",
                ),
                html.A(
                    children=[
                        html.Img(
                            src="assets/img/sun.png",  # Icône pour Rapports
                            style={"width": "40px", "margin": "20px 10px", "vertical-align": "middle"},
                        ),
                        html.Span("Ensoleillement", style={"margin-left": "10px", "font-size": "14px", "vertical-align": "middle", "display": "none"}),  # Span pour le texte
                    ],
                    href="/ensoleillement",
                ),
                html.A(
                    children=[
                        html.Img(
                            src="assets/img/thermometer.png",  # Icône pour Température
                            style={"width": "40px", "margin": "20px 10px", "vertical-align": "middle"},
                        ),
                        html.Span("Température", style={"margin-left": "10px", "font-size": "14px", "vertical-align": "middle", "display": "none"}),  # Span pour le texte
                    ],
                    href="/temperature",
                ),
                html.A(
                    children=[
                          html.Img(src="assets/img/inds.png", style={"width": "40px", "margin": "20px 10px", "vertical-align": "middle"}),
                          html.Span("Zones Industrielles", style={"margin-left": "10px", "font-size": "14px", "vertical-align": "middle", "display": "none"}),
                        ],
                      href="/zones-industrielles",
                ),
                html.A(
                    children=[
                        html.Img(
                            src="assets/img/rain.png",  # Icône pour Paramètres
                            style={"width": "40px", "margin": "20px 10px", "vertical-align": "middle"},
                        ),
                        html.Span("Précipitations", style={"margin-left": "10px", "font-size": "14px", "vertical-align": "middle", "display": "none"}),  # Span pour le texte
                    ],
                    href="/precipitations",
                ),
                html.A(
                    children=[
                        html.Img(
                            src="assets/img/lightning.png",  # Icône pour Paramètres
                            style={"width": "40px", "margin": "20px 10px", "vertical-align": "middle"},
                        ),
                        html.Span("Electricité", style={"margin-left": "10px", "font-size": "14px", "vertical-align": "middle", "display": "none"}),  # Span pour le texte
                    ],
                    href="/electricite",
                ),
                html.A(
                    children=[
                        html.Img(
                            src="assets/img/sun.png",  # Icône pour Optimisation
                            style={"width": "40px", "margin": "20px 10px", "vertical-align": "middle"},
                        ),
                        html.Span(
                            "Optimisation",
                            style={
                                "margin-left": "10px",
                                "font-size": "14px",
                                "vertical-align": "middle",
                                "display": "none",
                            },
                        ),
                    ],
                    href="/optimisation",
                ),
            ]
        ),
        
        # Bouton pour changer la taille
        html.Button(
            children=[
                html.Img(
                    src="assets/img/arrow.png",  # Icône de flèche
                    style={"width": "40px", "transition": "transform 0.3s"}  # Ajout de la transition de rotation
                ),
            ],
            id="toggle-width-btn",
            style={"margin-top": "20px", "padding": "12px", "background-color": "#ffffff", "color": "#005dff", "border": "none", "cursor": "pointer", "border-radius": "2em"},
        ),
    ],
)

##########################################################################################################################################
##########################################################################################################################################
######################              HTML conteneur main_content                                          #################################
##########################################################################################################################################
##########################################################################################################################################

##########################################################################################################################################
##########################################################################################################################################
######################              HTML conteneur ensoleillement                                        #################################
##########################################################################################################################################
##########################################################################################################################################
# Ensoleillement line chart graphe
fig_ens = go.Figure()
fig_ens.add_trace(go.Scatter(x=monthly_data.index.to_timestamp(), 
                              y=monthly_data['ensoleillement'], 
                              mode='lines+markers', 
                              name='Ensoleillement',
                              marker=dict(size=8),
                              line=dict(width=2)))
fig_ens.add_trace(go.Scatter(x=monthly_data.index.to_timestamp(), 
                              y=monthly_data['ensoleillement'].expanding().mean(), 
                              mode='lines', 
                              name='Avg Trend', 
                              line=dict(dash='dash', width=2)))
fig_ens.update_layout(
    xaxis_title='Month',
    yaxis_title='Ensoleillement (hours)',
    template='plotly_white',
    xaxis=dict(tickformat='%Y-%m'),
    yaxis=dict(showgrid=True, zeroline=True),
    legend=dict(title='Legend', x=0.01, y=0.99),
    title={
            "text": "Monthly Average Ensoleillement",
            "font": {
                "size": 22,
            },
            "x": 0.5,  # Centrer le titre horizontalement
    }
)
# Contenu ensoleillement
##########################################################################################################################################
##########################################################################################################################################
######################              HTML conteneur temperature                                           #################################
##########################################################################################################################################
##########################################################################################################################################
#graphe line chart temperature
fig_temp = go.Figure()
fig_temp.add_trace(go.Scatter(x=monthly_data.index.to_timestamp(), 
                              y=monthly_data['temperature'], 
                              mode='lines+markers', 
                              name='Temperature',
                              marker=dict(size=8),
                              line=dict(width=2)))
fig_temp.add_trace(go.Scatter(x=monthly_data.index.to_timestamp(), 
                              y=monthly_data['temperature'].expanding().mean(), 
                              mode='lines', 
                              name='Avg Trend', 
                              line=dict(dash='dash', width=2)))
fig_temp.update_layout(
    xaxis_title='Month',
    yaxis_title='Temperature (°C)',
    template='plotly_white',
    xaxis=dict(tickformat='%Y-%m'),
    yaxis=dict(showgrid=True, zeroline=True),
    legend=dict(title='Legend', x=0.01, y=0.99),
    title={
            "text": "Monthly Average Temperature",
            "font": {
                "size": 22,
            },
            "x": 0.5,  # Centrer le titre horizontalement
    }
)
# Contenu température

##########################################################################################################################################
##########################################################################################################################################
######################              HTML conteneur precipitation                                         #################################
##########################################################################################################################################
##########################################################################################################################################
fig_prec = go.Figure()
fig_prec.add_trace(go.Scatter(x=monthly_data.index.to_timestamp(), 
                               y=monthly_data['precipitation'], 
                               mode='lines+markers', 
                               name='Precipitation',
                               marker=dict(size=8),
                               line=dict(width=2)))
fig_prec.add_trace(go.Scatter(x=monthly_data.index.to_timestamp(), 
                               y=monthly_data['precipitation'].expanding().mean(), 
                               mode='lines', 
                               name='Avg Trend', 
                               line=dict(dash='dash', width=2)))
fig_prec.update_layout(
    xaxis_title='Month',
    yaxis_title='Precipitation (mm)',
    template='plotly_white',
    xaxis=dict(tickformat='%Y-%m'),
    yaxis=dict(showgrid=True, zeroline=True),
    legend=dict(title='Legend', x=0.01, y=0.99),
    title={
            "text": "Monthly Average Precipitation",
            "font": {
                "size": 22,
            },
            "x": 0.5,  # Centrer le titre horizontalement
    }
)
# Contenu Précipitations



##########################################################################################################################################
##########################################################################################################################################
##########################################################################################################################################
##########################################################################################################################################
######################              HTML conteneur optimisation                                       #################################
##########################################################################################################################################
##########################################################################################################################################

# Figure Mapbox : score global par point
fig_opt = px.scatter_mapbox(
    opt_points_sorted,
    lat="latitude",
    lon="longitude",
    color="score_global",
    size="score_global",
    hover_name=opt_points_sorted["adresse"] if "adresse" in opt_points_sorted.columns else opt_points_sorted["idpoint"].astype(str),
    hover_data={
        "idpoint": True,
        "score_global": ':.1f',
        "ensoleillement": ':.1f',
        "irradiance": ':.1f',
        "production": ':.1f',
        "precipitation": ':.1f',
        "temperature": ':.1f',
    },
    color_continuous_scale="YlOrRd",
    mapbox_style="open-street-map",
    zoom=10,
    center={
        "lat": float(opt_points_sorted["latitude"].mean()) if not opt_points_sorted.empty else 0,
        "lon": float(opt_points_sorted["longitude"].mean()) if not opt_points_sorted.empty else 0,
    },
)

fig_opt.update_layout(
    title={
        "text": "Score global d'optimalité pour l'installation de panneaux solaires",
        "font": {"size": 22},
        "x": 0.5,
    },
    margin={"r": 0, "t": 60, "l": 0, "b": 0},
)

# Tableau TOP 10 des meilleurs emplacements
top_rows = []
for _, row in top_opt_points.iterrows():
    top_rows.append(
        html.Tr(
            [
                html.Td(int(row["idpoint"])),
                html.Td(row.get("adresse", "-")),
                html.Td(f"{row['score_global']:.1f} %"),
            ]
        )
    )

top_points_table = html.Table(
    [
        html.Thead(
            html.Tr(
                [
                    html.Th("ID Point"),
                    html.Th("Adresse"),
                    html.Th("Score global"),
                ]
            )
        ),
        html.Tbody(top_rows),
    ],
    style={"width": "100%", "fontSize": "14px"},
)


######################              HTML conteneur electricité                                           #################################
##########################################################################################################################################
##########################################################################################################################################
fig_ratio = px.choropleth_mapbox(
    geojson={
        'type': 'FeatureCollection',
        'features': filtered_features
    },
    featureidkey="properties.name",
    locations=filtered_commune_names,
    color=filtered_ratio_values,
    color_continuous_scale="RdYlGn",
    mapbox_style="open-street-map",
    zoom=9,
    range_color=[0,10],
    center={"lat": 46.2044, "lon": 6.1432},
    title="Ratio Production/Consommation par Commune"
)

fig_ratio.update_traces(marker_line_width=2, marker_line_color="white")
figure_pie = go.Figure(
    data=[
        go.Pie(
            values=[77, 11, 12],
            labels=["Hydraulique", "Solaire", "Incinération des déchets"]
        )
    ]
)

# Mise à jour de la mise en page de la figure
figure_pie.update_layout(
    title="Production électricité du canton de Genève",
    plot_bgcolor='white',  # Fond du graphique en blanc
    paper_bgcolor='white',  # Fond extérieur en blanc
    title_font=dict(
        size=22,  # Taille du titre
    ),
    title_x=0.5  # Centrer le titre horizontalement
)


##########################################################################################################################################
##########################################################################################################################################
######################                                HTML conteneur profile                             #################################
##########################################################################################################################################
##########################################################################################################################################




# Disposition principale
app.layout = html.Div(
    style={
        "display": "flex",
        "height": "100vh",
        "width": "100vw",
        "margin": "0",
        "padding": "0",
        "overflow": "hidden",
    },
    children=[
        dcc.Store(id="sidebar-width", data="80px"),
        dcc.Store(id="chat-map-action"),
        vertical_header,
        html.Div(
            id="main-content",
            style={
                "padding": "20px 80px 0 80px",  # Ajoute un espace entre le header et le contenu principal
                "width": "100%",
                "flex": "1",
                "height": "100%",
                "overflowY": "auto",
            },
        ),
        get_chatbot_layout(),
        dcc.Location(id='url', refresh=False),
    ],
)





##########################################################################################################################################
##########################################################################################################################################
######################                        Callback                                                   #################################
##########################################################################################################################################
##########################################################################################################################################
# Callback pour changer le contenu principal en fonction de l'URL
@app.callback(
    Output('main-content', 'children'),
    Input('url', 'pathname')
)
def display_content(pathname):
    if pathname == '/':
        return render_main_content(global_means=global_means, map_production=map_production)
    elif pathname == "/home":
        return render_main_content(global_means=global_means, map_production=map_production)
    elif pathname == "/ensoleillement":
        return render_ensoleillement(df_mois=df_mois, fig_ens=fig_ens, map_ensoleillement=map_ensoleillement)
    elif pathname == "/temperature":
        return render_temperature(df_mois=df_mois, fig_temp=fig_temp, map_temperature=map_temperature)
    elif pathname == "/precipitations":
        return render_precipitations(df_mois=df_mois, fig_prec=fig_prec, map_precipitation=map_precipitation)
    elif pathname == "/electricite":
        return render_electricite(fig_ratio=fig_ratio, figure_pie=figure_pie)
    elif pathname == "/optimisation":
        return render_optimisation(fig_opt=fig_opt, top_points_table=top_points_table)
    elif pathname == "/zones-industrielles":  # ✅ Ajoutez cette ligne
        return render_zones_industrielles(map_zones_industrielles, zones_df)  # Utilisez les bonnes variables
    else:
        return html.H1("Page non trouvée")


# Callback pour changer la largeur de la barre latérale
@app.callback(
    [Output("vertical-header", "style"), Output("sidebar-width", "data"), Output("toggle-width-btn", "children")],
    Input("toggle-width-btn", "n_clicks"),
    State("sidebar-width", "data"),
    prevent_initial_call=True
)
def toggle_sidebar_width(n_clicks, current_width):
    new_width = "200px" if current_width == "80px" else "80px"
    updated_style = vertical_header_style.copy()
    updated_style["width"] = new_width

    # Gérer la rotation de la flèche
    rotate_style = {"transform": "rotate(180deg)"} if new_width == "200px" else {}

    # Mettre à jour les flèches et les spans
    new_children = [
        html.Img(
            src="assets/img/arrow.png",  # Icône de flèche
            style={**{"width": "40px"}, **rotate_style}  # Applique la rotation
        )
    ]

    return updated_style, new_width, new_children

# Callback pour gérer l'affichage des spans
@app.callback(
    Output("nav-menu", "children"),
    Input("sidebar-width", "data"),
    prevent_initial_call=True,
)
def update_menu_text_display(sidebar_width):
    if sidebar_width == '80px':
        return [
            html.A(children=[html.Img(src='assets/img/home.png', style={'width': '40px', 'margin': '20px 10px', 'vertical-align': 'middle'}), html.Span('Accueil', style={'margin-left': '10px', 'font-size': '14px', 'vertical-align': 'middle', 'display': 'none'})], href='/home'),
            html.A(children=[html.Img(src='assets/img/sun.png', style={'width': '40px', 'margin': '20px 10px', 'vertical-align': 'middle'}), html.Span('Ensoleillement', style={'margin-left': '10px', 'font-size': '14px', 'vertical-align': 'middle', 'display': 'none'})], href='/ensoleillement'),
            html.A(children=[html.Img(src='assets/img/thermometer.png', style={'width': '40px', 'margin': '20px 10px', 'vertical-align': 'middle'}), html.Span('Température', style={'margin-left': '10px', 'font-size': '14px', 'vertical-align': 'middle', 'display': 'none'})], href='/temperature'),
            html.A(children=[html.Img(src='assets/img/rain.png', style={'width': '40px', 'margin': '20px 10px', 'vertical-align': 'middle'}), html.Span('Précipitations', style={'margin-left': '10px', 'font-size': '14px', 'vertical-align': 'middle', 'display': 'none'})], href='#'),
            html.A(children=[html.Img(src='assets/img/lightning.png', style={'width': '40px', 'margin': '20px 10px', 'vertical-align': 'middle'}), html.Span('Electricité', style={'margin-left': '10px', 'font-size': '14px', 'vertical-align': 'middle', 'display': 'none'})], href='/electricite'),
            html.A(children=[html.Img(src='assets/img/sun.png', style={'width': '40px', 'margin': '20px 10px', 'vertical-align': 'middle'}), html.Span('Optimisation', style={'margin-left': '10px', 'font-size': '14px', 'vertical-align': 'middle', 'display': 'none'})], href='/optimisation'),
        ]
    else:
        return [
            html.A(children=[html.Img(src='assets/img/home.png', style={'width': '40px', 'margin': '20px 10px', 'vertical-align': 'middle'}), html.Span('Accueil', style={'margin-left': '10px', 'font-size': '18px', 'vertical-align': 'middle', 'display': 'inline', 'color': '#fff', 'font-size': '16px', 'outline': 'none'})], href='/home'),
            html.A(children=[html.Img(src='assets/img/sun.png', style={'width': '40px', 'margin': '20px 10px', 'vertical-align': 'middle'}), html.Span('Ensoleillement', style={'margin-left': '10px', 'font-size': '18px', 'vertical-align': 'middle', 'display': 'inline', 'color': '#fff', 'font-size': '16px', 'outline': 'none'})], href='/ensoleillement'),
            html.A(children=[html.Img(src='assets/img/thermometer.png', style={'width': '40px', 'margin': '20px 10px', 'vertical-align': 'middle'}), html.Span('Température', style={'margin-left': '10px', 'font-size': '18px', 'vertical-align': 'middle', 'display': 'inline', 'color': '#fff', 'font-size': '16px', 'outline': 'none'})], href='/temperature'),
            html.A(children=[html.Img(src='assets/img/rain.png', style={'width': '40px', 'margin': '20px 10px', 'vertical-align': 'middle'}), html.Span('Précipitations', style={'margin-left': '10px', 'font-size': '18px', 'vertical-align': 'middle', 'display': 'inline', 'color': '#fff', 'font-size': '16px', 'outline': 'none'})], href='/precipitations'),
            html.A(children=[html.Img(src='assets/img/lightning.png', style={'width': '40px', 'margin': '20px 10px', 'vertical-align': 'middle'}), html.Span('Electricité', style={'margin-left': '10px', 'font-size': '18px', 'vertical-align': 'middle', 'display': 'inline', 'color': '#fff', 'font-size': '16px', 'outline': 'none'})], href='electricite'),
            html.A(children=[html.Img(src='assets/img/sun.png', style={'width': '40px', 'margin': '20px 10px', 'vertical-align': 'middle'}), html.Span('Optimisation', style={'margin-left': '10px', 'font-size': '18px', 'vertical-align': 'middle', 'display': 'inline', 'color': '#fff', 'font-size': '16px', 'outline': 'none'})], href='/optimisation'),
        ]

from dash import callback_context

@app.callback(
    [Output('map-graph', 'figure'), Output('click-data', 'children')],
    [
        Input('map-graph', 'clickData'),
        Input('chat-map-action', 'data'),   # 👈 nouvelle entrée
    ],
    suppress_callback_exceptions=True,
)
def update_map(clickData, chat_action):
    # -----------------------------
    # 1) Déterminer la commune cible
    # -----------------------------
    commune_name = None
    ctx = callback_context

    if ctx.triggered:
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

        # 👉 Cas 1 : action venant du chatbot
        if trigger_id == "chat-map-action" and chat_action:
            # On attend un dict du type {"type": "commune", "name": "Meyrin", ...}
            if isinstance(chat_action, dict) and chat_action.get("type") == "commune":
                commune_name = chat_action.get("name")

        # 👉 Cas 2 : clic direct sur la carte
        elif trigger_id == "map-graph" and clickData:
            commune_name = clickData["points"][0]["location"]

    # -----------------------------
    # 2) Construction de la carte
    # -----------------------------
    # Communes présentes dans le GeoJSON
    commune_names = [ft["properties"]["name"] for ft in communes_geo_data]

    # Dictionnaire nom_commune → consommation
    consommation_dict = dict(zip(df["nom_commune"], df["consommation"]))

    # Liste des valeurs de consommation dans le même ordre que commune_names
    consommation_values = [consommation_dict.get(name, 0) for name in commune_names]

    fig = px.choropleth_mapbox(
        geojson={"type": "FeatureCollection", "features": communes_geo_data},
        featureidkey="properties.name",
        title="Consommation annuelle d'électricité en kWh",
        locations=commune_names,
        color=consommation_values,
        color_continuous_scale="Viridis",
        mapbox_style="open-street-map",
        center={"lat": 46.1833, "lon": 6.0833},
        zoom=10,
        range_color=[0, 7000],
    )

    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        title={"font": {"size": 22}, "x": 0.5},
    )
    fig.update_traces(marker_line_width=2, marker_line_color="white")

    # -----------------------------
    # 3) Info texte / zoom si commune ciblée
    # -----------------------------
    click_info = "Cliquez sur un polygone ou demandez une commune au chatbot."

    if commune_name:
        # On normalise un peu pour matcher la BDD
        commune_mask = df["nom_commune"].str.lower().str.strip() == commune_name.lower().strip()
        commune_data = df[commune_mask]

        # Option : zoom/coeur sur la commune si elle existe dans le geojson
        geo_match = [
            f
            for f in communes_geo_data
            if f["properties"].get("name", "").lower().strip()
            == commune_name.lower().strip()
        ]
        if geo_match:
            # On recentre la carte sur cette commune
            # (centre du bounding box approximatif)
            coords = geo_match[0]["geometry"]["coordinates"][0]
            lats = [c[1] for c in coords]
            lons = [c[0] for c in coords]
            fig.update_layout(
                mapbox_center={"lat": sum(lats) / len(lats), "lon": sum(lons) / len(lons)},
                mapbox_zoom=11,
            )

        if not commune_data.empty:
            consumption = commune_data["consommation"].iloc[0]
            year = commune_data["annee"].iloc[0]
            click_info = html.Div(
                [
                    html.P(f"Commune sélectionnée : {commune_name}"),
                    html.P(f"Consommation : {consumption} kWh"),
                    html.P(f"Année : {year}"),
                ]
            )
        else:
            click_info = html.Div(
                [
                    html.P(f"Commune sélectionnée : {commune_name}"),
                    html.P("Données non disponibles"),
                ]
            )

    return fig, click_info


# Callback pour rediriger vers la page Electricité quand le chatbot demande une commune
@app.callback(
    Output("url", "pathname"),
    Input("chat-map-action", "data"),
    prevent_initial_call=True,
)
def redirect_from_chat(chat_action):
    """Si le chatbot envoie une action de type 'commune',
    on bascule automatiquement vers la page /electricite.
    """
    if isinstance(chat_action, dict) and chat_action.get("type") == "commune":
        return "/electricite"
    return no_update


# Enregistrement des callbacks du chatbot
register_chatbot_callbacks(app)


# Exécution de l'application
if __name__ == "__main__":
    app.run(debug=False, host='0.0.0.0', port=8050)