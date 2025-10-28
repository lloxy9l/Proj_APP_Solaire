import json
import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from config_bdd import host, user, password, database
import mysql.connector
import pandas as pd
from ia_zones import extract_industrial_zones, get_zones_dataframe



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

##########################################################################################################################################
##########################################################################################################################################
######################              Conversion des données en DF pour les utiliser                       #################################
##########################################################################################################################################
##########################################################################################################################################
# Charger les données
data_meteo,data_conso,data_commune = fetch_data()

df = pd.DataFrame(data_meteo)
df_conso = pd.DataFrame(data_conso)
prod_df = pd.DataFrame(data_meteo)
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
communes_geo_data = get_communes_data(df, geojson_data)
print("Data communed fetched")

##########################################################################################################################################
##########################################################################################################################################
######################              Récupération zones industrielles avec IA                             #################################
##########################################################################################################################################
##########################################################################################################################################

# Charger les données des zones industrielles
print("Chargement des zones industrielles...")
zones_industrielles_gdf = extract_industrial_zones(zone="Geneva, Switzerland")
zones_df = get_zones_dataframe(zones_industrielles_gdf)
print("Zones industrielles chargées")
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
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])


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
                          html.Img(src="assets/img/industry.png", style={"width": "40px", "margin": "20px 10px", "vertical-align": "middle"}),
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
                            src="assets/img/team.png",  # Icône pour Rapports
                            style={"width": "40px", "margin": "20px 10px", "vertical-align": "middle"},
                        ),
                        html.Span("Crédits", style={"margin-left": "10px", "font-size": "14px", "vertical-align": "middle", "display": "none"}),  # Span pour le texte
                    ],
                    href="/credit",
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
main_content = html.Div(
    style={
        "padding": "20px 80px 0 80px",  # Ajoute un espace entre le header et le contenu principal
        "width": "100%",
    },
    id="main-content",  # Ajout d'un id pour changer dynamiquement le contenu

    children=[
        # Barre de recherche et photo de profil
        html.Div(
            style={
                "display": "flex",
                "justify-content": "space-between",  # Utilisation de space-between pour espacer les éléments
                "align-items": "center",  # Alignement vertical
                "margin-bottom": "20px",
            },
            children=[
                # Barre de recherche moderne
                html.Div(
                    style={
                        "position": "relative",  # Pour positionner l'icône à l'intérieur de l'input
                        "width": "50%",
                    },
                    children=[
                        html.Div(
                            style={
                                "position": "absolute",
                                "left": "10px",
                                "top": "50%",
                                "transform": "translateY(-50%)",
                            },
                            children=[
                                html.Img(
                                    src="assets/img/search-icon.png",
                                    style={"width": "30px", "height": "30px"},
                                ),
                            ],
                        ),
                        dcc.Input(
                            id="search-input",
                            type="text",
                            placeholder="Rechercher...",
                            style={
                                "width": "100%",
                                "padding": "10px 10px 10px 50px",
                                "border-radius": "2em",
                                "border": "2px solid #005DFF",
                                "background-color": "#f8f8f8",
                                "font-size": "18px",
                                "outline": "none",
                            },
                        ),
                    ],
                ),
                # Photo de profil
                html.A(
                    href="/profile_content",  # Remplacez par le lien voulu
                    children=html.Img(
                        src="assets/img/profile.png",
                        style={
                            "width": "65px",
                            "height": "65px",
                            "border-radius": "50%",
                            "border": "2px solid #fff",
                        },
                    )
                ),
            ],
        ),

        # Section des cartes pour les informations chiffrées
        html.Div(
            style={
                "display": "flex",
                "justify-content": "space-between",  # Utilisation de space-between pour espacer les éléments
                "align-items": "center",  # Alignement vertical
                "margin-bottom": "20px",
            },
            children=[
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                html.P("Température", className="card-title"),
                                html.H4(f"{global_means['temperature']:.2f}°C/jour", className="card-text"),
                            ]
                        ),
                    ],
                    style={"width": "18rem"},
                ),
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                html.P("Précipitations", className="card-title"),
                                html.H4(f"{global_means['precipitation']:.2f} mm/jour", className="card-text"),
                            ]
                        ),
                    ],
                    style={"width": "18rem"},
                ),
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                html.P("Ensoleillement", className="card-title"),
                                html.H4(f"{global_means['ensoleillement']:.2f} heures/jour", className="card-text"),
                            ]
                        ),
                    ],
                    style={"width": "18rem"},
                ),
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                html.P("Irradiance", className="card-title"),
                                html.H4(f"{global_means['irradiance']:.2f} W/m²/jour", className="card-text"),
                            ]
                        ),
                    ],
                    style={"width": "18rem"},
                ),
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                html.P("Consommation éléctrique moyenne", className="card-title"),
                                html.H4(f"{global_means['consommation']:.2f} GWh/année", className="card-text"),
                            ]
                        ),
                    ],
                ),
            ],
        ),

        # Section des cartes pour les graphiques
        html.Div(
            style={
                "width":"100%",
                "height":"calc(100vh-350px)",
            },
            children=[
                # Première ligne - 1 colonne
                dbc.Card(
                [
                    dbc.CardBody(
                        [
                            dcc.Graph(
                                id="graph-1",
                                figure=px.scatter_mapbox(
                                    mean_data,
                                    title="Production d'electricité estimée en KWh",
                                    lat="latitude",
                                    lon="longitude",
                                    color="production",  # Affichage basé sur la température moyenne
                                    color_continuous_scale="RdYlGn",  # Palette de couleurs
                                    hover_data=["production"],  # Infos affichées au survol
                                    size=[1 for _ in range(len(mean_data))],
                                    mapbox_style="carto-positron",
                                    center=dict(lat=46.2047, lon=6.14231),  # Centrer sur Genève
                                ).update_layout(
                                    title={
                                        "text": "Production d'electricité estimée en KWh",
                                        "font": {"size": 26,},  # Taille et gras du titre
                                        "x": 0.5,  # Centrer le titre horizontalement
                                    }
                                ),
                                style={
                                    "cursor": "url('assets/img/panneau.png') 4 12, crosshair",
                                    "width": "100%",
                                    "height": "calc(100vh - 350px)",
                                },
                            )
                        ]
                    ),
                ]
                ),
            ],
        ),
    ],
)

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
ensoleillement_content = html.Div(
    style={
        "padding": "20px 80px 0 80px",  # Ajoute un espace entre le header et le contenu principal
        "width": "100%",
    },
    id="main-content",  # Ajout d'un id pour changer dynamiquement le contenu
    
    children=[
        # Barre de recherche et photo de profil
        html.Div(
            style={
                "display": "flex",
                "justify-content": "space-between",  # Utilisation de space-between pour espacer les éléments
                "align-items": "center",  # Alignement vertical
                "margin-bottom": "20px",
            },
            children=[
                # Barre de recherche moderne
                html.Div(
                    style={
                        "position": "relative",  # Pour positionner l'icône à l'intérieur de l'input
                        "width": "50%",
                    },
                    children=[
                        html.Div(
                            style={
                                "position": "absolute",
                                "left": "10px",
                                "top": "50%",
                                "transform": "translateY(-50%)",
                            },
                            children=[ 
                                html.Img(
                                    src="assets/img/search-icon.png",
                                    style={"width": "30px", "height": "30px"},
                                ),
                            ],
                        ),
                        dcc.Input(
                            id="search-input",
                            type="text",
                            placeholder="Rechercher...",
                            style={
                                "width": "100%",
                                "padding": "10px 10px 10px 50px",
                                "border-radius": "2em",
                                "border": "2px solid #005DFF",
                                "background-color": "#f8f8f8",
                                "font-size": "18px",
                                "outline": "none",
                            },
                        ),
                    ],
                ),
                # Photo de profil
                html.A(
                    href="/profile_content",  # Remplacez par le lien voulu
                    children=html.Img(
                        src="assets/img/profile.png",
                        style={
                            "width": "65px",
                            "height": "65px",
                            "border-radius": "50%",
                            "border": "2px solid #fff",
                        },
                    )
                ),
            ],
        ),
        
        # Titre de la section
        html.H1(
            "Ensoleillement",  # Nom de la page
            style={
                "font-size": "36px",  # Taille de la police
                "margin-bottom": "20px",  # Espace en dessous du titre
            },
        ),
        
        # Section des cartes pour les graphiques - 1 seule colonne pour la première ligne, 3 colonnes pour la deuxième ligne
        html.Div(
            style={
                "display": "grid",
                "grid-template-columns": "1fr",  # 1 seule colonne sur la première ligne
                "gap": "20px",  # Espacement entre les cartes
            },
            children=[
                # Première carte (ligne 1)
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                               dcc.Graph(
                                    id="v",
                                    figure=px.scatter_mapbox(
                                        mean_data,
                                        title="Ensoleillement quotidien moyen en heures",
                                        lat="latitude",
                                        lon="longitude",
                                        color="ensoleillement",  # Affichage basé sur l'ensoleillement
                                        color_continuous_scale="Plasma",  # Palette de couleurs
                                        hover_data=["ensoleillement"],  # Infos affichées au survol
                                        size=[200 for _ in range(len(mean_data))],
                                        mapbox_style="carto-positron",
                                        center=dict(lat=46.2047, lon=6.14231),  # Centrer sur Genève
                                    ).update_layout(
                                    title={
                                        "text": "Ensoleillement quotidien moyen en heures",
                                        "font": {"size": 26,},  # Taille et gras du titre
                                        "x": 0.5,  # Centrer le titre horizontalement
                                    }
                                ),
                                    style={"width":"100%", "height":"calc(100vh - 350px)",},
                                )
                            ]
                        ),
                    ]
                ),
            ],
        ),
        
        # Deuxième ligne - 2 colonnes
        html.Div(
            style={
                "display": "grid",
                "grid-template-columns": "repeat(2, 1fr)",  # 2 colonnes
                "gap": "20px",  # Espacement entre les cartes
                "margin-top":"20px",
                "margin-bottom": "20px",
                "height":"50vh"
            },
            children=[
                # Deuxième carte
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                dcc.Graph(
                                    id="graph-2",
                                    figure=fig_ens,
                                    style={"width": "100%", "height": "100%"},
                                )
                            ]
                        ),
                    ]
                ),
                
                # Troisième carte
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                dcc.Graph(
                                    id="graph-3",
                                    figure = px.bar(
                                        df_mois,
                                        x="mois",
                                        y="ensoleillement",
                                        title="Distribution des heures d'ensoleillement par mois",
                                        labels={"ensoleillement": "Heures d'ensoleillement", "mois": "Mois"},
                                        color="ensoleillement",  # Utilisation d'une échelle de couleur pour l'ensoleillement
                                        color_continuous_scale="Plasma",
                                    ).update_layout(
                                        plot_bgcolor='white',  # Fond du graphique en blanc
                                        paper_bgcolor='white',  # Fond extérieur en blanc
                                        title={
                                        "font": {"size": 22,},  # Taille et gras du titre
                                        "x": 0.5,  # Centrer le titre horizontalement
                                    }

                                    ),
                                    style={"width": "100%", "height": "100%"},
                                )
                            ]
                        ),
                    ]
                ),
            ],
        ),
    ],
)
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
temperature_content = html.Div(
    style={
        "padding": "20px 80px 0 80px",  # Ajoute un espace entre le header et le contenu principal
        "width": "100%",
    },
    id="main-content",  # Ajout d'un id pour changer dynamiquement le contenu
    
    children=[
        # Barre de recherche et photo de profil
        html.Div(
            style={
                "display": "flex",
                "justify-content": "space-between",  # Utilisation de space-between pour espacer les éléments
                "align-items": "center",  # Alignement vertical
                "margin-bottom": "20px",
            },
            children=[
                # Barre de recherche moderne
                html.Div(
                    style={
                        "position": "relative",  # Pour positionner l'icône à l'intérieur de l'input
                        "width": "50%",
                    },
                    children=[
                        html.Div(
                            style={
                                "position": "absolute",
                                "left": "10px",
                                "top": "50%",
                                "transform": "translateY(-50%)",
                            },
                            children=[ 
                                html.Img(
                                    src="assets/img/search-icon.png",
                                    style={"width": "30px", "height": "30px"},
                                ),
                            ],
                        ),
                        dcc.Input(
                            id="search-input",
                            type="text",
                            placeholder="Rechercher...",
                            style={
                                "width": "100%",
                                "padding": "10px 10px 10px 50px",
                                "border-radius": "2em",
                                "border": "2px solid #005DFF",
                                "background-color": "#f8f8f8",
                                "font-size": "18px",
                                "outline": "none",
                            },
                        ),
                    ],
                ),
                # Photo de profil
                html.A(
                    href="/profile_content",  # Remplacez par le lien voulu
                    children=html.Img(
                        src="assets/img/profile.png",
                        style={
                            "width": "65px",
                            "height": "65px",
                            "border-radius": "50%",
                            "border": "2px solid #fff",
                        },
                    )
                ),
            ],
        ),
        html.H1(
            "Temperature",  # Nom de la page
            style={
                "font-size": "36px",  # Taille de la police
                "margin-bottom": "20px",  # Espace en dessous du titre
            },
        ),
        
        # Section des cartes pour les graphiques - 1 seule colonne pour la première ligne, 3 colonnes pour la deuxième ligne
        html.Div(
            style={
                "display": "grid",
                "grid-template-columns": "1fr",  # 1 seule colonne sur la première ligne
                "gap": "20px",  # Espacement entre les cartes
            },
            children=[
                # Première carte (ligne 1)
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                dcc.Graph(
                                    id="graph-1",
                                    figure=px.scatter_mapbox(
                                        mean_data,
                                        title="Température quotidienne moyenne en °C",
                                        lat="latitude",
                                        lon="longitude",
                                        color="temperature",  # Affichage basé sur la température moyenne
                                        color_continuous_scale="Plasma",  # Palette de couleurs
                                        hover_data=["temperature"],  # Infos affichées au survol
                                        size=[200 for _ in range(len(mean_data))],
                                        mapbox_style="carto-positron",
                                        center=dict(lat=46.2047, lon=6.14231),  # Centrer sur Genève
                                    ).update_layout(
                                    title={
                                        "font": {"size": 26,},  # Taille et gras du titre
                                        "x": 0.5,  # Centrer le titre horizontalement
                                    }
                                ),
                                    style={"width":"100%", "height":"calc(100vh - 350px)",},
                                )
                            ]
                        ),
                    ]
                ),
            ],
        ),
        
        # Deuxième ligne - 3 colonnes
        html.Div(
            style={
                "display": "grid",
                "grid-template-columns": "repeat(2, 1fr)",  # 2 colonnes
                "gap": "20px",  # Espacement entre les cartes
                "margin-top":"20px",
                "height":"50vh"
            },
            children=[
                # Deuxième carte
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                dcc.Graph(
                                    id="graph-2",
                                    
                                    figure=fig_temp,
                                    style={"width": "100%", "height": "100%"},
                                ),
                            ]
                        ),
                    ]
                ),
                
                # Troisième carte
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                dcc.Graph(
                                    id="graph-3",
                                    figure = px.bar(
                                        df_mois,
                                        x="mois",
                                        y="temperature",
                                        title="Distribution des temperature par mois",
                                        labels={"temperature": "Temperature en °C", "mois": "Mois"},
                                        color="temperature",  # Utilisation d'une échelle de couleur pour la temperature
                                        color_continuous_scale="Plasma",
                                    ).update_layout(
                                        plot_bgcolor='white',  # Fond du graphique en blanc
                                        paper_bgcolor='white',  # Fond extérieur en blanc
                                        title={
                                        "font": {"size": 22,},  # Taille et gras du titre
                                        "x": 0.5,  # Centrer le titre horizontalement
                                    }
                                    ),
                                    style={"width": "100%", "height": "100%"},
                                )
                            ]
                        ),
                    ]
                ),
            ],
        ),
    ],
)

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
precipitations_content = html.Div(
    style={
        "padding": "20px 80px 0 80px",  # Ajoute un espace entre le header et le contenu principal
        "width": "100%",
    },
    id="main-content",  # Ajout d'un id pour changer dynamiquement le contenu
    
    children=[
        # Barre de recherche et photo de profil
        html.Div(
            style={
                "display": "flex",
                "justify-content": "space-between",  # Utilisation de space-between pour espacer les éléments
                "align-items": "center",  # Alignement vertical
                "margin-bottom": "20px",
            },
            children=[
                # Barre de recherche moderne
                html.Div(
                    style={
                        "position": "relative",  # Pour positionner l'icône à l'intérieur de l'input
                        "width": "50%",
                    },
                    children=[
                        html.Div(
                            style={
                                "position": "absolute",
                                "left": "10px",
                                "top": "50%",
                                "transform": "translateY(-50%)",
                            },
                            children=[
                                html.Img(
                                    src="assets/img/search-icon.png",
                                    style={"width": "30px", "height": "30px"},
                                ),
                            ],
                        ),
                        dcc.Input(
                            id="search-input",
                            type="text",
                            placeholder="Rechercher...",
                            style={
                                "width": "100%",
                                "padding": "10px 10px 10px 50px",
                                "border-radius": "2em",
                                "border": "2px solid #005DFF",
                                "background-color": "#f8f8f8",
                                "font-size": "18px",
                                "outline": "none",
                            },
                        ),
                    ],
                ),
                # Photo de profil
                html.A(
                    href="/profile_content",  # Remplacez par le lien voulu
                    children=html.Img(
                        src="assets/img/profile.png",
                        style={
                            "width": "65px",
                            "height": "65px",
                            "border-radius": "50%",
                            "border": "2px solid #fff",
                        },
                    )
                ),
            ],
        ),
        
        # Titre de la section
        html.H1(
            "Précipitations",  # Nom de la page
            style={
                "font-size": "36px",  # Taille de la police
                "margin-bottom": "20px",  # Espace en dessous du titre
            },
        ),
        
        # Section des cartes pour les graphiques en 1x3 pour la première ligne, puis 3 colonnes sur la deuxième ligne
        html.Div(
            style={
                "display": "grid",
                "grid-template-columns": "1fr",  # 1 seule colonne sur la première ligne
                "gap": "20px",  # Espacement entre les cartes
                "margin-bottom": "20px",
            },
            children=[
                # Première carte (ligne 1)
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                               dcc.Graph(
                                    id="graph-1",
                                    figure=px.scatter_mapbox(
                                        mean_data,
                                        title="Précipitation quotidienne moyenne en mm",
                                        lat="latitude",
                                        lon="longitude",
                                        color="precipitation",  # Affichage basé sur la précipitation
                                        color_continuous_scale=["#a9cce3", "#5499c7", "#2471a3", "#1f618d", "#243852"],  # Palette de couleurs
                                        hover_data=["precipitation"],  # Infos affichées au survol
                                        size=[200 for _ in range(len(mean_data))],
                                        mapbox_style="carto-positron",
                                        center=dict(lat=46.2047, lon=6.14231),  # Centrer sur Genève
                                    ).update_layout(
                                    title={
                                        "font": {"size": 26,},  # Taille et gras du titre
                                        "x": 0.5,  # Centrer le titre horizontalement
                                    }
                                ),
                                    style={"width":"100%", "height":"calc(100vh - 350px)",},
                                )
                            ]
                        ),
                    ]
                ),
            ],
        ),
        
        # Deuxième ligne - 3 colonnes
        html.Div(
            style={
                "display": "grid",
                "grid-template-columns": "repeat(2, 1fr)",  # 3 colonnes
                "gap": "20px",  # Espacement entre les cartes
                "margin-top": "20px",
                "margin-bottom": "20px",
                "height":"50vh",
            },
            children=[
                # Deuxième carte
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                dcc.Graph(
                                    id="graph-2",
                                    figure=fig_prec,
                                    style={"width": "100%", "height": "100%"},
                                ),
                            ]
                        ),
                    ]
                ),
                
                # Troisième carte
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                dcc.Graph(
                                    id="graph-3",
                                    figure = px.bar(
                                        df_mois,
                                        x="mois",
                                        y="precipitation",
                                        title="Distribution des precipitation par mois",
                                        labels={"Precipitation": "Precipitation en mm", "mois": "Mois"},
                                        color="precipitation",  # Utilisation d'une échelle de couleur pour la precipitation
                                        color_continuous_scale=["#a9cce3", "#5499c7", "#2471a3", "#1f618d", "#243852"],
                                        
                                    ).update_layout(
                                        plot_bgcolor='white',  # Fond du graphique en blanc
                                        paper_bgcolor='white',  # Fond extérieur en blanc
                                        title={
                                        "font": {"size": 22,},  # Taille et gras du titre
                                        "x": 0.5,  # Centrer le titre horizontalement
                                    }
                                    ),
                                    style={"width": "100%", "height": "100%"},
                                )
                            ]
                        ),
                    ]
                ),
            ],
        ),
    ],
)



##########################################################################################################################################
##########################################################################################################################################
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

electricite_content = html.Div(
    style={
        "padding": "20px 80px 0 80px",  # Ajoute un espace entre le header et le contenu principal
        "width": "100%",
    },
    id="main-content",  # Ajout d'un id pour changer dynamiquement le contenu
    
    children=[
        # Barre de recherche et photo de profil
        html.Div(
            style={
                "display": "flex",
                "justify-content": "space-between",  # Utilisation de space-between pour espacer les éléments
                "align-items": "center",  # Alignement vertical
                "margin-bottom": "20px",
            },
            children=[
                # Barre de recherche moderne
                html.Div(
                    style={
                        "position": "relative",  # Pour positionner l'icône à l'intérieur de l'input
                        "width": "50%",
                    },
                    children=[
                        html.Div(
                            style={
                                "position": "absolute",
                                "left": "10px",
                                "top": "50%",
                                "transform": "translateY(-50%)",
                            },
                            children=[
                                html.Img(
                                    src="assets/img/search-icon.png",
                                    style={"width": "30px", "height": "30px"},
                                ),
                            ],
                        ),
                        dcc.Input(
                            id="search-input",
                            type="text",
                            placeholder="Rechercher...",
                            style={
                                "width": "100%",
                                "padding": "10px 10px 10px 50px",
                                "border-radius": "2em",
                                "border": "2px solid #005DFF",
                                "background-color": "#f8f8f8",
                                "font-size": "18px",
                                "outline": "none",
                            },
                        ),
                    ],
                ),
                # Photo de profil
                html.A(
                    href="/profile_content",  # Remplacez par le lien voulu
                    children=html.Img(
                        src="assets/img/profile.png",
                        style={
                            "width": "65px",
                            "height": "65px",
                            "border-radius": "50%",
                            "border": "2px solid #fff",
                        },
                    )
                ),
            ],
        ),
        html.H1(
            "Electricité",  # Nom de la page
            style={
                "font-size": "36px",  # Taille de la police
                "margin-bottom": "20px",  # Espace en dessous du titre
            },
        ),        # Section des cartes pour les graphiques en 3x3
        html.Div(
            style={
                "display": "grid",
                "grid-template-columns": "1fr",  # 1 seule colonne sur la première ligne
                "gap": "20px",  # Espace entre les cartes
            },
            children = [
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                dcc.Graph(
                                    id='map-graph',
                                    
                                    style={
                                        'height': 'calc(100vh - 350px)',
                                        'width': '100%'
                                    }
                                ),
                                html.Div(
                                    id='click-data',
                                    style={
                                        'padding': '5px',
                                        'font-size': '20px'
                                    }
                                )
                            ]
                        ),
                    ]
                ),
            ]

        ),
        # Deuxième ligne - 3 colonnes
        html.Div(
            style={
                "display": "grid",
                "grid-template-columns": "repeat(2, 1fr)",  # 3 colonnes
                "gap": "20px",  # Espacement entre les cartes
                "margin-top": "20px",
            },
            children=[
                # Deuxième carte
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                dcc.Graph(
                                    id="graph-2",
                                    figure=figure_pie,
                                )
                            ]
                        ),
                    ]
                ),
                
                # Troisième carte
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                dcc.Graph(
                                    id="graph-3",
                                    figure=fig_ratio.update_layout(
                                        plot_bgcolor='white',  # Fond du graphique en blanc
                                        paper_bgcolor='white',  # Fond extérieur en blanc
                                        title={
                                        "font": {"size": 22,},  # Taille et gras du titre
                                        "x": 0.5,  # Centrer le titre horizontalement
                                        }
                                    )
                                )
                            ]
                        ),
                    ]
                ),
            ],
        ),
    ],
)


##########################################################################################################################################
##########################################################################################################################################
######################              HTML conteneur zones industrielles                                   #################################
##########################################################################################################################################
##########################################################################################################################################

# Graphique pour la distribution des zones
fig_zones_distribution = px.histogram(
    zones_df,
    x="niveau_adaptabilite",
    title="Distribution des zones par niveau d'adaptabilité",
    color="niveau_adaptabilite",
    color_discrete_map={
        "Adaptée": "#2ecc71",
        "Moyenne": "#f39c12",
        "Non adaptée": "#e74c3c"
    }
).update_layout(
    plot_bgcolor='white',
    paper_bgcolor='white',
    title={
        "font": {"size": 22},
        "x": 0.5
    },
    xaxis_title="Niveau d'adaptabilité",
    yaxis_title="Nombre de zones"
)

# Graphique pour le potentiel de production
fig_production_zones = px.bar(
    zones_df.nlargest(10, 'production_potentielle'),
    x="name",
    y="production_potentielle",
    title="Top 10 des zones à plus fort potentiel de production",
    color="production_potentielle",
    color_continuous_scale="Greens"
).update_layout(
    plot_bgcolor='white',
    paper_bgcolor='white',
    title={
        "font": {"size": 22},
        "x": 0.5
    },
    xaxis_title="Zone",
    yaxis_title="Production potentielle (MWh/an)"
)

zones_industrielles_content = html.Div(
    style={
        "padding": "20px 80px 0 80px",
        "width": "100%",
    },
    id="main-content",
    children=[
        # Barre de recherche et photo de profil
        html.Div(
            style={
                "display": "flex",
                "justify-content": "space-between",
                "align-items": "center",
                "margin-bottom": "20px",
            },
            children=[
                html.Div(
                    style={
                        "position": "relative",
                        "width": "50%",
                    },
                    children=[
                        html.Div(
                            style={
                                "position": "absolute",
                                "left": "10px",
                                "top": "50%",
                                "transform": "translateY(-50%)",
                            },
                            children=[
                                html.Img(
                                    src="assets/img/search-icon.png",
                                    style={"width": "30px", "height": "30px"},
                                ),
                            ],
                        ),
                        # dcc.Input(
                        #     id="search-input",
                        #     type="text",
                        #     placeholder="Rechercher...",
                        #     style={
                        #         "width": "100%",
                        #         "padding": "10px 10px 10px 50px",
                        #         "border-radius": "2em",
                        #         "border": "2px solid #005DFF",
                        #         "background-color": "#f8f8f8",
                        #         "font-size": "18px",
                        #         "outline": "none",
                        #     },
                        # ),
                    ],
                ),
                html.A(
                    href="/profile_content",
                    children=html.Img(
                        src="assets/img/profile.png",
                        style={
                            "width": "65px",
                            "height": "65px",
                            "border-radius": "50%",
                            "border": "2px solid #fff",
                        },
                    )
                ),
            ],
        ),
        
        # Titre
        html.H1(
            "Zones Industrielles - Potentiel Solaire",
            style={
                "font-size": "36px",
                "margin-bottom": "20px",
            },
        ),
        
        # Carte principale
        html.Div(
            style={
                "display": "grid",
                "grid-template-columns": "1fr",
                "gap": "20px",
            },
            children=[
                dbc.Card([
                    dbc.CardBody([
                        dcc.Graph(
                            id="zones-map",
                            figure=px.scatter_mapbox(
                                zones_df,
                                lat="latitude",
                                lon="longitude",
                                color="niveau_adaptabilite",
                                size="surface_m2",
                                hover_data={
                                    "name": True,
                                    "surface_m2": ":.0f",
                                    "production_potentielle": ":.2f",
                                    "latitude": False,
                                    "longitude": False
                                },
                                color_discrete_map={
                                    "Adaptée": "#2ecc71",
                                    "Moyenne": "#f39c12",
                                    "Non adaptée": "#e74c3c"
                                },
                                title="Zones industrielles adaptées pour panneaux solaires",
                                mapbox_style="carto-positron",
                                center=dict(lat=46.2047, lon=6.14231),
                                zoom=11
                            ).update_layout(
                                title={
                                    "text": "Zones industrielles - Adaptabilité pour panneaux solaires",
                                    "font": {"size": 26},
                                    "x": 0.5
                                }
                            ),
                            style={"width": "100%", "height": "calc(100vh - 350px)"}
                        )
                    ])
                ])
            ]
        ),
        
        # Graphiques secondaires
        html.Div(
            style={
                "display": "grid",
                "grid-template-columns": "repeat(2, 1fr)",
                "gap": "20px",
                "margin-top": "20px",
                "margin-bottom": "20px",
                "height": "50vh"
            },
            children=[
                dbc.Card([
                    dbc.CardBody([
                        dcc.Graph(
                            id="zones-distribution",
                            figure=fig_zones_distribution,
                            style={"width": "100%", "height": "100%"}
                        )
                    ])
                ]),
                dbc.Card([
                    dbc.CardBody([
                        dcc.Graph(
                            id="zones-production",
                            figure=fig_production_zones,
                            style={"width": "100%", "height": "100%"}
                        )
                    ])
                ])
            ]
        )
    ]
)

##########################################################################################################################################
##########################################################################################################################################
######################                                HTML conteneur profile                             #################################
##########################################################################################################################################
##########################################################################################################################################
#Profile content
profile_content = html.Div(
    style={
        "margin-left": "80px",
        "padding": "20px",
        "display": "flex",
        "justify-content": "center",
        "align-items": "center",
        "height": "810px",
        "width": "917px",
        "background-color": "#005dff",
        "border-radius": "30px",
        "position": "absolute",
        "top": "50%",
        "left": "50%",
        "transform": "translate(-50%, -50%)",
    },
    children=[
        html.Div(
            style={
                "background-color": "white",
                "padding": "30px",
                "border-radius": "10px",
                "width": "800px",
                "height": "705px",
                "box-shadow": "0 4px 6px rgba(0, 0, 0, 0.1)"
            },
            children=[
                # Título e imagem do usuário
                html.Div(
                    style={"margin-top": "10px"},
                    children=[
                        html.Div(
                            style={"display": "flex", "align-items": "center"},
                            children=[
                                # Imagem do usuário
                                html.Div(
                                    style={
                                        "position": "relative",
                                        "width": "120px",
                                        "height": "120px",
                                        "border-radius": "50%",
                                        "background-image": "url('assets/img/user_image.png')",
                                        "background-size": "cover",
                                        "background-position": "center",
                                        "border": "3px solid white",
                                    },
                                    children=[
                                        # Ícone de editar imagem
                                        html.Div(
                                            style={
                                                "position": "absolute",
                                                "bottom": "5px",
                                                "right": "5px",
                                                "background-color": "#005dff",
                                                "border-radius": "50%",
                                                "padding": "5px",
                                                "background-image": "url('assets/svg/edit.svg')",
                                            },
                                            children=[
                                                html.Img(
                                                    src="assets/edit-icon.png",
                                                    style={"width": "20px", "height": "20px"},
                                                ),
                                            ],
                                        ),
                                    ],
                                ),
                                # Nome e email do usuário
                                html.Div(
                                    style={"margin-left": "15px"},
                                    children=[
                                        html.H3("User Name", style={"margin-bottom": "5px"}),
                                        html.P("useremail@example.com", style={"color": "#888"}),
                                    ]
                                ),
                            ]
                        ),
                    ]
                ),
                html.Hr(style={"border": "none", "border-top": "1px solid #ddd", "box-shadow": "0 2px 4px rgba(0, 0, 0, 0.1)", "margin": "5px 0"}),

                # Detalhes do usuário
                html.Div(
                    style={"margin-top": "20px"},
                    children=[
                        html.Div(
                            style={"display": "flex", "justify-content": "space-between"},
                            children=[
                                html.Label("Name", style={"font-size": "20px", "text-shadow": "2px 2px 5px rgba(0, 0, 0, 0.2)"}),
                                html.P("Your Name", style={"margin-bottom": "15px", "margin-left": "10px", "font-size": "20px", "text-shadow": "2px 2px 5px rgba(0, 0, 0, 0.2)"})
                            ]
                        ),
                        html.Hr(style={"border": "none", "border-top": "1px solid #ddd", "box-shadow": "0 2px 4px rgba(0, 0, 0, 0.1)", "margin": "5px 0"}),

                        # Email
                        html.Div(
                            style={"display": "flex", "justify-content": "space-between"},
                            children=[
                                html.Label("Email account", style={"font-size": "20px", "text-shadow": "2px 2px 5px rgba(0, 0, 0, 0.2)"}),
                                html.P("yourname@gmail.com", style={"margin-bottom": "15px", "font-size": "20px", "text-shadow": "2px 2px 5px rgba(0, 0, 0, 0.2)"})
                            ]
                        ),
                        html.Hr(style={"border": "none", "border-top": "1px solid #ddd", "box-shadow": "0 2px 4px rgba(0, 0, 0, 0.1)", "margin": "5px 0"}),

                        # Telefone
                        html.Div(
                            style={"display": "flex", "justify-content": "space-between"},
                            children=[
                                html.Label("Mobile number", style={"font-size": "20px", "text-shadow": "2px 2px 5px rgba(0, 0, 0, 0.2)"}),
                                html.P("Add number", style={"margin-bottom": "15px", "font-size": "20px", "text-shadow": "2px 2px 5px rgba(0, 0, 0, 0.2)"})
                            ]
                        ),
                        html.Hr(style={"border": "none", "border-top": "1px solid #ddd", "box-shadow": "0 2px 4px rgba(0, 0, 0, 0.1)", "margin": "5px 0"}),

                        # Localização
                        html.Div(
                            style={"display": "flex", "justify-content": "space-between"},
                            children=[
                                html.Label("Location", style={"font-size": "20px", "text-shadow": "2px 2px 5px rgba(0, 0, 0, 0.2)"}),
                                html.P("USA", style={"margin-bottom": "15px", "font-size": "20px", "text-shadow": "2px 2px 5px rgba(0, 0, 0, 0.2)"})
                            ]
                        ),
                        html.Hr(style={"border": "none", "border-top": "1px solid #ddd", "box-shadow": "0 2px 4px rgba(0, 0, 0, 0.1)", "margin": "5px 0"}),

                        # Password
                        html.Div(
                            style={"display": "flex", "justify-content": "space-between"},
                            children=[
                                html.Label("Password", style={"font-size": "20px", "text-shadow": "2px 2px 5px rgba(0, 0, 0, 0.2)"}),
                                html.P("*********", style={"margin-bottom": "15px", "font-size": "20px", "text-shadow": "2px 2px 5px rgba(0, 0, 0, 0.2)"})
                            ]
                        ),
                    ]
                ),
                
                # Botão de "Save Changes"
                html.Div(
                    style={"display": "flex", "justify-content": "center", "margin-top": "30px"},
                    children=[
                        html.Button(
                            "Save Changes",
                            style={
                                "background-color": "#2489FF",
                                "color": "white",
                                "padding": "10px 30px",
                                "border": "none",
                                "border-radius": "6px",
                                "cursor": "pointer",
                                "font-size": "18px",
                            }
                        ),
                    ]
                ),
            ]
        )
    ]
)


credit_content = html.Div(
    style={
        "margin-left": "80px",
        "padding": "20px",
        "display": "flex",
        "justify-content": "center",
        "align-items": "center",
        "height": "810px",
        "width": "917px",
        "background-color": "#005dff",
        "border-radius": "30px",
        "position": "absolute",
        "top": "50%",
        "left": "50%",
        "transform": "translate(-50%, -50%)",
    },
    children=[
        html.Div(
            style={
                "background-color": "white",
                "padding": "30px",
                "border-radius": "10px",
                "width": "800px",
                "height": "705px",
                "box-shadow": "0 4px 6px rgba(0, 0, 0, 0.1)"
            },
            children=[
                # Titre de la page
                html.Div(
                    style={"text-align": "center", "margin-bottom": "20px"},
                    children=[
                        html.H1("Geneva Weather Data Collection", style={"color": "#005dff"}),
                        html.P(
                            "Projet réalisé par un groupe d'étudiants pour collecter et analyser les données météorologiques de la région de Genève.",
                            style={"color": "#555"}
                        )
                    ]
                ),

                # Description du projet
                html.Div(
                    style={"margin-bottom": "20px"},
                    children=[
                        html.H2("Introduction", style={"color": "#005dff"}),
                        html.P(
                            "Ce projet vise à collecter des données météorologiques détaillées et fiables pour la région de Genève. Ces données sont essentielles pour des applications comme la planification urbaine, l'agriculture, et les projets d'énergie renouvelable."
                        ),
                        html.H2("Objectifs", style={"color": "#005dff"}),
                        html.Ul([
                            html.Li("Collecter des données sur la luminosité, la radiance, la température et les précipitations."),
                            html.Li("Fournir des informations exploitables pour les parties prenantes locales."),
                            html.Li("Créer une base de données robuste pour le stockage sécurisé des données.")
                        ])
                    ]
                ),

                # Liste des membres de l'équipe
                html.Div(
                    style={"margin-bottom": "20px"},
                    children=[
                        html.H2("Équipe", style={"color": "#005dff"}),
                        html.Ul([
                            html.Li("Maxens Soldan"),
                            html.Li("Baptiste Renand"),
                            html.Li("Arno Wilhelm"),
                            html.Li("Degouey Corentin"),
                            html.Li("Hassnaoui Walid"),
                            html.Li("Bercier Thomas"),
                            html.Li("Francielle Andrade Cardoso")
                        ]),
                        html.P("Coryright 2025")
                    ]
                ),
            ]
        )
    ]
)


# Disposition principale
app.layout = html.Div(
    style={"display": "flex"},
    children=[
        dcc.Store(id="sidebar-width", data="80px"),  # Stocker la largeur actuelle de la barre latérale
        vertical_header,
        main_content,
        dcc.Location(id='url', refresh=False),  # Composant Location pour détecter l'URL
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
        return main_content
    elif pathname == "/home":
        return main_content
    elif pathname == "/ensoleillement":
        return ensoleillement_content
    elif pathname == "/temperature":
        return temperature_content
    elif pathname == "/precipitations":
        return precipitations_content
    elif pathname == "/electricite":
        return electricite_content
    elif pathname == "/profile_content":
        return profile_content
    elif pathname =="/credit":
        return credit_content
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
    # Si la largeur est réduite, on cache les spans
    if sidebar_width == "80px":
        # Retourne le menu avec les spans cachés
        return [
            html.A(
                children=[
                    html.Img(src="assets/img/home.png", style={"width": "40px", "margin": "20px 10px", "vertical-align": "middle"}),
                    html.Span("Accueil", style={"margin-left": "10px", "font-size": "14px", "vertical-align": "middle", "display": "none"}),
                ],
                href="/home",
            ),
            html.A(
                children=[
                    html.Img(src="assets/img/sun.png", style={"width": "40px", "margin": "20px 10px", "vertical-align": "middle"}),
                    html.Span("Ensoleillement", style={"margin-left": "10px", "font-size": "14px", "vertical-align": "middle", "display": "none"}),
                ],
                href="/ensoleillement",
            ),
            html.A(
                children=[
                    html.Img(src="assets/img/thermometer.png", style={"width": "40px", "margin": "20px 10px", "vertical-align": "middle"}),
                    html.Span("Température", style={"margin-left": "10px", "font-size": "14px", "vertical-align": "middle", "display": "none"}),
                ],
                href="/temperature",
            ),
            html.A(
                children=[
                    html.Img(src="assets/img/rain.png", style={"width": "40px", "margin": "20px 10px", "vertical-align": "middle"}),
                    html.Span("Précipitations", style={"margin-left": "10px", "font-size": "14px", "vertical-align": "middle", "display": "none"}),
                ],
                href="#",
            ),
            html.A(
                children=[
                    html.Img(src="assets/img/lightning.png", style={"width": "40px", "margin": "20px 10px", "vertical-align": "middle"}),
                    html.Span("Electricité", style={"margin-left": "10px", "font-size": "14px", "vertical-align": "middle", "display": "none"}),
                ],
                href="/electricite",
            ),
            html.A(
                children=[
                    html.Img(src="assets/img/team.png", style={"width": "40px", "margin": "20px 10px", "vertical-align": "middle"}),
                    html.Span("Crédits", style={"margin-left": "10px", "font-size": "14px", "vertical-align": "middle", "display": "none"}),
                ],
                href="/credit",
            ),
        ]
    else:
        # Si la largeur est agrandie, on montre les spans
        return [
            html.A(
                children=[
                    html.Img(src="assets/img/home.png", style={"width": "40px", "margin": "20px 10px", "vertical-align": "middle"}),
                    html.Span("Accueil", style={"margin-left": "10px", "font-size": "18px", "vertical-align": "middle", "display": "inline", "color": "#fff", "font-size": "16px", "outline": "none"}),
                ],
                href="/home",
            ),
            html.A(
                children=[
                    html.Img(src="assets/img/sun.png", style={"width": "40px", "margin": "20px 10px", "vertical-align": "middle"}),
                    html.Span("Ensoleillement", style={"margin-left": "10px", "font-size": "18px", "vertical-align": "middle", "display": "inline", "color": "#fff", "font-size": "16px", "outline": "none"}),
                ],
                href="/ensoleillement",
            ),
            html.A(
                children=[
                    html.Img(src="assets/img/thermometer.png", style={"width": "40px", "margin": "20px 10px", "vertical-align": "middle"}),
                    html.Span("Température", style={"margin-left": "10px", "font-size": "18px", "vertical-align": "middle", "display": "inline", "color": "#fff", "font-size": "16px", "outline": "none"}),
                ],
                href="/temperature",
            ),
            html.A(
                children=[
                    html.Img(src="assets/img/rain.png", style={"width": "40px", "margin": "20px 10px", "vertical-align": "middle"}),
                    html.Span("Précipitations", style={"margin-left": "10px", "font-size": "18px", "vertical-align": "middle", "display": "inline", "color": "#fff", "font-size": "16px", "outline": "none"}),
                ],
                href="/precipitations",
            ),
            html.A(
                children=[
                    html.Img(src="assets/img/lightning.png", style={"width": "40px", "margin": "20px 10px", "vertical-align": "middle"}),
                    html.Span("Electricité", style={"margin-left": "10px", "font-size": "18px", "vertical-align": "middle", "display": "inline", "color": "#fff", "font-size": "16px", "outline": "none"}),
                ],
                href="electricite",
            ),
            html.A(
                children=[
                    html.Img(src="assets/img/team.png", style={"width": "40px", "margin": "20px 10px", "vertical-align": "middle"}),
                    html.Span("Crédits", style={"margin-left": "10px", "font-size": "18px", "vertical-align": "middle", "display": "inline", "color": "#fff", "font-size": "16px", "outline": "none"}),
                ],
                href="credit",
            ),
            
        ]

# Callback pour mettre à jour la carte et gérer les clics sur les zones
@app.callback(
    
    [Output('map-graph', 'figure'), Output('click-data', 'children')],
    [Input('map-graph', 'clickData')],
    suppress_callback_exceptions=True,
    
)
def update_map(clickData):
    # Définir une valeur par défaut pour 'commune_name' s'il n'y a pas encore de clic
    commune_name = None
    if clickData:
        commune_name = clickData['points'][0]['location']

    # Préparer les données pour la carte
    commune_names = [ft['properties']['name'] for ft in communes_geo_data]
    
    # Extraire les consommations pour chaque commune dans la même ordre que les noms
    consommation_dict = dict(zip(df['nom_commune'], df['consommation']))
    
    # Utiliser les valeurs de consommation, avec une valeur par défaut si la consommation est manquante
    consommation_values = [consommation_dict.get(name, 0) for name in commune_names]
    
    # Création de la carte avec les polygones colorés en fonction de la consommation
    fig = px.choropleth_mapbox(
        geojson={'type': 'FeatureCollection', 'features': communes_geo_data},
        featureidkey="properties.name",  # Identifier par le nom de la commune
        title="Consommation annuelle d'electricité en KWh",
        locations=commune_names,  # Communes du GeoJSON
        color=consommation_values,  # Coloration par la consommation d'électricité
        color_continuous_scale="Viridis",  # Utilisation d'une échelle de couleur continue
        mapbox_style="open-street-map",
        zoom=9.3,
        range_color=[0,7000],
        center={"lat": 46.1833, "lon": 6.0833}  # Centré sur Genève
    )
    fig.update_layout(
        plot_bgcolor='white',  # Fond du graphique en blanc
        paper_bgcolor='white',  # Fond extérieur en blanc
        title={
        "font": {"size": 22,},  # Taille et gras du titre
        "x": 0.5,  # Centrer le titre horizontalement
        }
    )

    # Personnaliser l'apparence des polygones
    fig.update_traces(marker_line_width=2, marker_line_color="white")

    # Initialiser le message d'information
    click_info = "Cliquez sur un polygone pour plus d'informations"
    
    # Si un clic a été détecté sur un polygone
    if commune_name:
        # Récupérer les données associées à la commune sélectionnée
        commune_data = df[df['nom_commune'] == commune_name]
        if not commune_data.empty:
            consumption = commune_data['consommation'].iloc[0]
            year = commune_data['annee'].iloc[0]
            click_info = html.Div([
                html.P(f"Commune sélectionnée : {commune_name}"),
                html.P(f"Consommation : {consumption} kWh"),
                html.P(f"Année : {year}")
            ])
        else:
            click_info = html.Div([
                html.P(f"Commune sélectionnée : {commune_name}"),
                html.P("Données non disponibles")
            ])

    return fig, click_info

# Exécution de l'application
if __name__ == "__main__":
    app.run_server(debug=False)