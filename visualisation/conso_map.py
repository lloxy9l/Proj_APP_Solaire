import dash
from dash import html, dcc, Input, Output
import dash_leaflet as dl
from datetime import datetime
from config_bdd import host, user, password, database
import mysql.connector
from geopy.geocoders import Nominatim
import time

geolocator = Nominatim(user_agent="your_app_name")

def get_coordinates_from_commune(commune_name):
    try:
        location = geolocator.geocode(commune_name)
        if location:
            return location.latitude, location.longitude
        else:
            return None, None
    except Exception as e:
        print(f"Erreur pour {commune_name}: {e}")
        return None, None

# Mise à jour de la fonction de récupération des données
def fetch_consommation_data_with_geocoding():
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

    # Ajouter les coordonnées de chaque commune
    for row in data:
        latitude, longitude = get_coordinates_from_commune(row["nom_commune"])
        row["latitude"] = latitude
        row["longitude"] = longitude
        #time.sleep(1)  # Pause pour respecter les limitations de l'API
    return data


consommation_data = fetch_consommation_data_with_geocoding()

# Structure des données par commune pour les années 2022 et 2023
commune_data = {}
for row in consommation_data:
    commune = row["nom_commune"]
    if commune not in commune_data:
        commune_data[commune] = {
            "latitude": row["latitude"],
            "longitude": row["longitude"],
            "2022": None,
            "2023": None
        }
    commune_data[commune][str(row["annee"])] = row["consommation"]

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
        children=[dl.TileLayer()],
        style={'width': '100%', 'height': '500px'},
        center=(46.2047, 6.14231),  # Centré sur Genève
        zoom=8
    )
])

@app.callback(
    Output("consommation-map", "children"),
    Input("year-dropdown", "value")
)
def update_map(selected_year):
    markers = []
    for commune, info in commune_data.items():
        # Gestion des consommations manquantes
        consommation_2022 = f"{info['2022']:,} kWh" if info["2022"] is not None else "Non disponible"
        consommation_2023 = f"{info['2023']:,} kWh" if info["2023"] is not None else "Non disponible"

        # Contenu du popup
        popup_content = f"Commune : {commune}\n"
        if selected_year == "2022" or selected_year == "all":
            popup_content += f"Consommation 2022 : {consommation_2022}\n"
        if selected_year == "2023" or selected_year == "all":
            popup_content += f"Consommation 2023 : {consommation_2023}\n"

        # Vérifier les coordonnées avant de créer un marqueur
        if info["latitude"] is not None and info["longitude"] is not None:
            markers.append(
                dl.Marker(
                    position=[info["latitude"], info["longitude"]],
                    children=dl.Popup(popup_content)
                )
            )

    # Ajouter les marqueurs et la couche de carte
    return [
        dl.TileLayer(
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        ),
        dl.LayerGroup(markers)
    ]

# Lancer l'application
if __name__ == '__main__':
    app.run_server(debug=True)
