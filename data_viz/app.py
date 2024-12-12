import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import mysql.connector

from config_bdd import host, user, password, database

# Connexion à la base de données MySQL
def get_data(days):
    conn = mysql.connector.connect(
        host=host,    # L'adresse de ton serveur MySQL
        user=user,   # Nom d'utilisateur MySQL
        password=password,  # Mot de passe MySQL
        database=database   # Nom de la base de données
    )
    
    # Requête SQL pour récupérer la moyenne d'irradiance sur X derniers jours
    query = f"""
    SELECT latitude, longitude, adresse, AVG(irradiance) as moyenne_irradiance, date_collecte
    FROM 2026_solarx_pointsgps 
    NATURAL JOIN 2026_solarx_mesures
    WHERE date_collecte >= CURDATE() - INTERVAL {days} YEAR
    GROUP BY latitude, longitude
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# Initialiser l'application Dash
app = dash.Dash(__name__)

# Layout de l'application Dash
app.layout = html.Div(children=[
    html.H1(children='Carte Interactive des Moyennes d\'Irradiance'),

    # Dropdown pour sélectionner la période de temps
    html.Label("Sélectionnez la période :"),
    dcc.Dropdown(
        id='time_period',
        options=[
            {'label': '1 an', 'value': 1},
            {'label': '3 ans', 'value': 3},
            {'label': '5 ans', 'value': 5}
        ],
        value=1,  # Valeur par défaut
        clearable=False
    ),

    # Graphique de la carte
    dcc.Graph(id='map')
])

# Callback pour mettre à jour la carte en fonction de la sélection de la période
@app.callback(
    Output('map', 'figure'),
    Input('time_period', 'value')
)
def update_map(years):
    # Obtenir les données filtrées par la période sélectionnée
    df = get_data(years)
    
    # Créer la carte avec des taches colorées en fonction de la moyenne d'irradiance
    fig = px.density_mapbox(
        df,
        lat="latitude",
        lon="longitude",
        z="moyenne_irradiance",
        radius=10,  # Rayon des taches colorées
        hover_name="adresse",
        hover_data={'moyenne_irradiance': True, 'date_collecte': True},
        zoom=6,  # Zoom initial
        color_continuous_scale=px.colors.sequential.Viridis,
        mapbox_style="open-street-map"
    )
    
    return fig

# Lancer l'application
if __name__ == '__main__':
    app.run_server(debug=True)