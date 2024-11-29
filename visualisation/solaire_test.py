import dash
from dash import html, dcc, Input, Output
import dash_leaflet as dl
from datetime import datetime
from config_bdd import host, user, password, database
import mysql.connector

# Fonction pour récupérer les données
def fetch_data():
    conn = mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database,
        charset="utf8"
    )
    with conn.cursor(dictionary=True) as c:
        c.execute("""
            SELECT p.latitude, p.longitude, m.temperature, 
                   m.ensoleillement, m.date_collecte 
            FROM 2026_solarx_pointsgps p
            JOIN 2026_solarx_mesures m 
            ON p.idpoint = m.idpoint;
        """)
        data = c.fetchall()
    conn.close()
    
    # Convertir `date_collecte` en datetime et gérer les valeurs None
    for row in data:
        row["date_collecte"] = datetime.strptime(row["date_collecte"], "%Y-%m-%d %H:%M:%S")
        
        # Vérifier si la valeur n'est pas None avant de convertir en float
        row["temperature"] = float(row["temperature"]) if row["temperature"] is not None else -666
        row["ensoleillement"] = float(row["ensoleillement"]) if row["ensoleillement"] is not None else -666
    
    return data

# Charger les données depuis la base
data = fetch_data()

# Extraire les plages de dates pour le sélecteur
unique_dates = sorted({row["date_collecte"].strftime("%Y-%m-%d") for row in data})
date_map = {date: i for i, date in enumerate(unique_dates)}  # Date à index

# Application Dash
app = dash.Dash(__name__)

# Mise en page
app.layout = html.Div([
    # Affichage du slider de date
    html.Div([
        html.Label("Sélectionnez une date :"),
        dcc.Slider(
            id='date-slider',
            min=0,
            max=len(unique_dates) - 1,
            step=1,
            marks={i: unique_dates[i] for i in range(len(unique_dates))},
            value=0  # La première date est sélectionnée par défaut
        ),
        html.Div(id="date-display", style={'margin-top': '10px'})
    ], style={'margin-bottom': '20px'}),

    # Carte Dash Leaflet
    dl.Map(
        id="map",
        children=[dl.TileLayer()],
        style={'width': '100%', 'height': '500px'},
        center=(46.2047, 6.14231),  # Centre sur Genève
        zoom=12
    )
])

# Callback pour mettre à jour les marqueurs en fonction de la date sélectionnée
@app.callback(
    [Output("map", "children"),
     Output("date-display", "children")],
    Input("date-slider", "value")
)
def update_map(selected_index):
    selected_date = unique_dates[selected_index]
    
    # Filtrer les données pour la date sélectionnée
    filtered_data = [
        row for row in data if row["date_collecte"].strftime("%Y-%m-%d") == selected_date
    ]
    
    # Créer les marqueurs
    markers = [
        dl.Marker(
            position=[row["latitude"], row["longitude"]],
            children=dl.Popup(
                f"Température : {round(row['temperature'], 1)}°C\n"
                f"Ensoleillement : {round(row['ensoleillement'], 2)} W/m²"
            )
        )
        for row in filtered_data
    ]

    # Mettre à jour l'affichage de la date sélectionnée
    date_display = f"Date sélectionnée : {selected_date}"

    # Retourner les éléments mis à jour pour la carte et l'affichage de la date
    return [dl.TileLayer(), dl.LayerGroup(markers)], date_display


# Lancer l'application
if __name__ == '__main__':
    app.run_server(debug=True)
