import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import mysql.connector
import json

from config_bdd import host, user, password, database

# Connexion à la base de données MySQL
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

# Initialisation de l'application Dash
app = dash.Dash(__name__)

# Chargement du fichier GeoJSON et des données communes
geojson_data = load_geojson('data_viz/geo_data_boundaries.geojson')
df = get_data()
communes_geo_data = get_communes_data(df, geojson_data)

# Layout de l'application
app.layout = html.Div([
    dcc.Graph(id='map-graph', style={'height': '800px'}),
    html.Div(id='click-data', style={'padding': '20px', 'font-size': '20px'})
])

# Callback pour mettre à jour la carte et gérer les clics sur les zones
@app.callback(
    [Output('map-graph', 'figure'), Output('click-data', 'children')],
    [Input('map-graph', 'clickData')]
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
        locations=commune_names,  # Communes du GeoJSON
        color=consommation_values,  # Coloration par la consommation d'électricité
        color_continuous_scale="Viridis",  # Utilisation d'une échelle de couleur continue
        mapbox_style="open-street-map",
        zoom=10,
        center={"lat": 46.2044, "lon": 6.1432}  # Centré sur Genève
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

# Exécution de l'application Dash
if __name__ == '__main__':
    app.run_server(debug=True)