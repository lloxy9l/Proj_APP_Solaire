import json
import dash
from dash import html, dcc, Input, Output
import dash_leaflet as dl
from config_bdd import host, user, password, database
import mysql.connector

# Charger le fichier GeoJSON existant
with open("communes_haute_savoie_geneve.geojson", "r", encoding="utf-8") as f:
    geojson_data = json.load(f)

# Charger les données de consommation
def fetch_consommation_data():
    conn = mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database,
        charset="utf8",
    )
    with conn.cursor(dictionary=True) as c:
        c.execute("""
            SELECT c.nom_commune, c.consommation, c.annee
            FROM 2026_solarx_consommation c
            WHERE c.annee IN (2022, 2023);
        """)
        data = c.fetchall()
    conn.close()

    # Organisation des données par commune
    consommation_data = {}
    for row in data:
        commune = row["nom_commune"]
        if commune not in consommation_data:
            consommation_data[commune] = {}
        consommation_data[commune][str(row["annee"])] = row["consommation"]
    return consommation_data

# Enrichir les données GeoJSON avec les consommations
consommation_data = fetch_consommation_data()
for feature in geojson_data["features"]:
    commune_name = feature["properties"]["name"]
    if commune_name in consommation_data:
        feature["properties"]["consommation"] = consommation_data[commune_name]

# Initialiser l'application Dash
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Carte des Consommations par Commune"),
    dcc.Dropdown(
        id="year-dropdown",
        options=[
            {"label": "2022", "value": "2022"},
            {"label": "2023", "value": "2023"},
            {"label": "Toutes les années", "value": "all"}
        ],
        value="all",
        clearable=False
    ),
    dl.Map(
        id="consommation-map",
        children=[
            dl.TileLayer(),
            dl.GeoJSON(
                id="geojson-layer",
                data=geojson_data,
                zoomToBounds=True,  # Zoom automatique sur les polygones
                options=dict(style=dict(color="blue", fillColor="cyan", weight=2, opacity=0.5))
            )
        ],
        style={'width': '100%', 'height': '500px'},
        center=(46.2047, 6.14231),  # Centré sur Genève
        zoom=8
    )
])

@app.callback(
    Output("geojson-layer", "data"),
    Input("year-dropdown", "value")
)
def update_geojson(selected_year):
    # Filtrer les données par année
    filtered_features = []
    for feature in geojson_data["features"]:
        properties = feature["properties"]
        consommation = properties.get("consommation", {})
        
        if selected_year == "all" or selected_year in consommation:
            filtered_features.append(feature)

    return {"type": "FeatureCollection", "features": filtered_features}

# Lancer l'application
if __name__ == "__main__":
    app.run_server(debug=True)
