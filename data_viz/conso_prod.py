import dash
from dash import dcc, html
from dash.dependencies import Output, Input
import plotly.express as px
import pandas as pd
import mysql.connector
import json

# Paramètres de la base de données
from config_bdd import host, user, password, database

def get_db_data(query):
    # Établir la connexion
    conn = mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database,
        charset="utf8",
    )
    
    # Lire les données avec pandas
    df = pd.read_sql(query, conn)
    
    # Fermer la connexion
    conn.close()
    
    return df

def get_conso_data():
    """
    Récupère la consommation des communes.
    """
    query = """
    SELECT nom_commune, consommation, annee
    FROM 2026_solarx_consommation
    """
    return get_db_data(query)

def get_prod_data():
    """
    Récupère la production estimée des communes.
    """
    query = """
    SELECT latitude, longitude, irradiance, adresse, date_collecte 
    FROM 2026_solarx_pointsgps
    JOIN 2026_solarx_mesures 
    ON 2026_solarx_pointsgps.idpoint = 2026_solarx_mesures.idpoint
    """
    return get_db_data(query)

def load_geojson(filepath):
    """
    Charge le fichier GeoJSON contenant les polygones des communes.
    
    :param filepath: Chemin vers le fichier GeoJSON.
    :return: Les données du fichier GeoJSON.
    """
    with open(filepath, 'r', encoding='utf-8') as file:
        geojson_data = json.load(file)
    return geojson_data

def extract_commune_from_adresse(adresse):
    """
    Extrait le nom de la commune depuis la colonne 'adresse'.
    
    :param adresse: Chaîne de caractère contenant l'adresse.
    :return: Nom de la commune (partie après la première virgule).
    """
    try:
        return adresse.split(',')
    except IndexError:
        return None

def assign_communes_to_prod_df(prod_df):
    """
    Ajoute une colonne 'ville' à prod_df avec les noms des communes extraits
    depuis la colonne 'adresse'.
    
    :param prod_df: DataFrame contenant les données de production.
    :return: DataFrame avec une colonne 'ville' ajoutée.
    """
    prod_df['ville'] = prod_df['adresse'].apply(extract_commune_from_adresse)
    return prod_df

def calculer_ratio(prod_df, conso_df):
    """
    Calcule le ratio production/consommation pour chaque ville présente dans les DataFrames.
    
    :param prod_df: DataFrame contenant les données de production (avec des colonnes 'latitude', 'longitude', 'adresse', et 'irradiance').
    :param conso_df: DataFrame contenant les données de consommation (avec des colonnes 'nom_commune' et 'consommation').
    :return: Un dictionnaire avec le ratio production/consommation pour chaque ville.
    """
    # Associer les noms des villes à prod_df à partir de l'adresse
    prod_df = assign_communes_to_prod_df(prod_df)

    # Filtrer les données pour éviter les valeurs manquantes ou incorrectes
    prod_df_clean = prod_df.dropna(subset=['ville', 'irradiance'])
    conso_df_clean = conso_df.dropna(subset=['nom_commune', 'consommation'])

    # Conversion de l'irradiance en numérique pour éviter les erreurs
    prod_df_clean['irradiance'] = pd.to_numeric(prod_df_clean['irradiance'], errors='coerce')

    # Calcul du ratio production/consommation pour chaque ville
    ratio_dict = {}
    for commune in conso_df_clean['nom_commune'].unique():
        # Récupérer la consommation pour la commune
        consommation = conso_df_clean[conso_df_clean['nom_commune'] == commune]['consommation'].sum()
        
        # Récupérer l'irradiance moyenne pour la commune
        mean_irradiance = prod_df_clean[prod_df_clean['ville'] == commune]['irradiance'].mean() * 365 * 3
        
        # Assurer que nous avons des données pour les deux (consommation et production)
        if consommation > 0 and mean_irradiance > 0:
            ratio_dict[commune] = mean_irradiance / consommation
    
    return ratio_dict

# Initialisation de l'application Dash
app = dash.Dash(__name__)

# Charger les fichiers de données et le fichier GeoJSON
geojson_data = load_geojson('data_viz/geo_data_boundaries.geojson')
conso_df = get_conso_data()
prod_df = get_prod_data()

# Calculer le ratio production/consommation pour chaque commune
ratio_dict = calculer_ratio(prod_df, conso_df)

# Layout de l'application
app.layout = html.Div([
    dcc.Graph(id='map-graph', style={'height': '800px'}),
    dcc.Interval(
        id='interval-component',
        interval=10*1000,  # Mise à jour toutes les 10 secondes
        n_intervals=0
    )
])

# Callback pour mettre à jour la carte
@app.callback(
    Output('map-graph', 'figure'),
    Input('interval-component', 'n_intervals')
)
def update_map(n_intervals):
    # Extraire les noms des communes et leurs ratios production/consommation
    commune_names = [ft['properties'].get('name', 'Inconnu') for ft in geojson_data['features']]
    ratio_values = [ratio_dict.get(name, 0) for name in commune_names]

    # Filtrer pour ne garder que les communes dont le ratio est supérieur à 0
    filtered_commune_names = [name for name, ratio in zip(commune_names, ratio_values) if ratio > 0]
    filtered_ratio_values = [ratio for ratio in ratio_values if ratio > 0]

    # Création de la carte avec les polygones colorés en fonction du ratio production/consommation
    fig = px.choropleth_mapbox(
        geojson={'type': 'FeatureCollection', 'features': geojson_data['features']},
        featureidkey="properties.name",  # Identifier par le nom de la commune
        locations=filtered_commune_names,  # Communes du GeoJSON
        color=filtered_ratio_values,  # Coloration par le ratio prod/conso
        color_continuous_scale="Viridis",  # Utilisation d'une échelle de couleur continue
        mapbox_style="open-street-map",
        zoom=10,
        center={"lat": 46.2044, "lon": 6.1432}  # Centré sur Genève
    )

    # Personnaliser l'apparence des polygones
    fig.update_traces(
        marker_line_width=2,
        marker_line_color="white",
        opacity=0.5
    )

    return fig

# Exécution de l'application Dash
if __name__ == '__main__':
    app.run_server(debug=True)