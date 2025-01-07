import dash
from dash import html, dcc, Input, Output
import plotly.express as px
from datetime import datetime
from config_bdd import host, user, password, database
import mysql.connector
import pandas as pd

# Fonction pour récupérer les données
def fetch_data():
    conn = mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database,
        charset="utf8",
    )
    with conn.cursor(dictionary=True) as c:
        c.execute("""
            SELECT p.latitude, p.longitude, m.temperature, 
                   m.ensoleillement,m.irradiance,m.precipitation, m.date_collecte 
            FROM 2026_solarx_pointsgps p
            JOIN 2026_solarx_mesures m 
            ON p.idpoint = m.idpoint;
        """)
        data = c.fetchall()
    conn.close()
    
    # Convertir les données en DataFrame
    df = pd.DataFrame(data)
    df["date_collecte"] = pd.to_datetime(df["date_collecte"])
    df["temperature"] = pd.to_numeric(df["temperature"], errors='coerce')
    df["irradiance"] = pd.to_numeric(df["irradiance"], errors='coerce')
    df["precipitation"] = pd.to_numeric(df["precipitation"], errors='coerce')
    df["ensoleillement"] = pd.to_numeric(df["ensoleillement"], errors='coerce')
    return df
print('Data collected')
# Charger les données
data = fetch_data()
df = pd.DataFrame(data)
# Extraire les dates uniques pour le sélecteur
unique_dates = sorted(data["date_collecte"].dt.strftime("%Y-%m-%d").unique())
print('Data Fetched')
# Application Dash
app = dash.Dash(__name__)

# Mise en page
app.layout = html.Div([
    # Sélecteur de date
    html.Div([
        html.Label("Sélectionnez une date :"),
        dcc.Slider(
            id='date-slider',
            min=0,
            max=len(unique_dates) - 1,
            step=1,
            marks={i: date for i, date in enumerate(unique_dates)},
            value=0
        ),
        html.Div(id="date-display", style={'margin-top': '10px'})
    ], style={'margin-bottom': '20px'}),

    # Carte Plotly
    dcc.Graph(id='map', style={'width': '100%', 'height': '600px'})
])

# Callback pour mettre à jour la heatmap
@app.callback(
    [Output('map', 'figure'),
     Output('date-display', 'children')],
    Input('date-slider', 'value')
)
def update_map(selected_index):
    selected_date = unique_dates[selected_index]

    # Filtrer les données pour la date sélectionnée
    filtered_data = df[df["date_collecte"].dt.strftime("%Y-%m-%d") == selected_date]

    value="ensoleillement" #a changer avec le callback 
    
    # Créer la carte avec scatter_mapbox
    fig = px.scatter_mapbox(
        filtered_data,
        lat="latitude",
        lon="longitude",
        color=value,  # Coloration par température a changer avec le callback
        color_continuous_scale="Plasma",  # Échelle de couleur
        hover_data=[value],  # Données affichées au survol
        center=dict(lat=46.2047, lon=6.14231),
        mapbox_style="carto-positron",
        size=[1 for _ in range(len(filtered_data))] 
    )

    # Mettre à jour l'affichage de la date sélectionnée
    date_display = f"Date sélectionnée : {selected_date}"

    return fig, date_display

# Lancer l'application
if __name__ == '__main__':
    app.run_server(debug=True)
