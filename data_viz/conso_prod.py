import dash
from dash import dcc, html
import plotly.express as px
import pandas as pd
import mysql.connector
import json
from config_bdd import host, user, password, database

# Charger les données géospatiales
with open('data_viz/geo_data_boundaries.geojson', 'r', encoding='utf-8') as file:
    geojson_data = json.load(file)

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
    df["production"] = df["irradiance"] * 365 * 3

    conso_df = pd.DataFrame(data_conso)
    conso_df["consommation"] = pd.to_numeric(conso_df["consommation"], errors='coerce')

    print("Data collected")
    return df, conso_df, data_point

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





# Initialisation de l'application Dash
app = dash.Dash(__name__)

# Chargement des données
data_meteo, data_conso, data_commune = fetch_data()

prod_df = pd.DataFrame(data_meteo)
conso_df = pd.DataFrame(data_conso)
commune_df = pd.DataFrame(data_commune)

# Calculer le ratio
ratio_dict = calculer_ratio(prod_df, conso_df, commune_df)

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

fig = px.choropleth_mapbox(
    geojson={
        'type': 'FeatureCollection',
        'features': filtered_features
    },
    featureidkey="properties.name",
    locations=filtered_commune_names,
    color=filtered_ratio_values,
    color_continuous_scale="RdYlGn",
    mapbox_style="open-street-map",
    zoom=10,
    range_color=[0,10],
    center={"lat": 46.2044, "lon": 6.1432},
    title="Ratio Production/Consommation par Commune"
)

fig.update_traces(marker_line_width=2, marker_line_color="white")

# Layout de l'application Dash
app.layout = html.Div([
    html.H1("Carte des Ratios Production/Consommation par Commune", style={'text-align': 'center'}),
    dcc.Graph(id='map-graph', figure=fig, style={'height': '800px'}),
])

# Exécution de l'application
if __name__ == '__main__':
    app.run_server(debug=True)
