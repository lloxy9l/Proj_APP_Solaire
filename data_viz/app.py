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
    
    # Requête SQL pour récupérer la moyenne d'irradiance sur les derniers jours
    query = f"""
    SELECT latitude, longitude, adresse, AVG(irradiance) as moyenne_irradiance, date_collecte
    FROM 2026_solarx_pointsgps 
    NATURAL JOIN 2026_solarx_mesures
    WHERE date_collecte >= CURDATE() - INTERVAL {days} DAY
    GROUP BY latitude, longitude
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# Initialiser l'application Dash
app = dash.Dash(__name__)

# Layout de l'application Dash
app.layout = html.Div(children=[
    html.H1(children="Carte Interactive des Moyennes d'Irradiance"),

    # Dropdown pour sélectionner la période de temps
    html.Label("Sélectionnez la période :"),
    dcc.Dropdown(
        id='time_period',
        options=[
            {'label': '1 an', 'value': 365},
            {'label': '3 ans', 'value': 3*365},
            {'label': '5 ans', 'value': 5*365}
        ],
        value=365,  # Valeur par défaut (1 an)
        clearable=False
    ),

    # Graphique de la carte avec hauteur définie
    dcc.Graph(
        id='map',
        style={'height': '1500px'}  # Modifier la hauteur ici (exemple : 600px)
    )
])

# Callback pour mettre à jour la carte en fonction de la sélection de la période
@app.callback(
    Output('map', 'figure'),
    Input('time_period', 'value')
)
def update_map(days):
    # Obtenir les données filtrées par la période sélectionnée
    df = get_data(days)
    
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
    
    # Ajout de l'option pour permettre le zoom via le scroll
    fig.update_layout(
        uirevision='constant',  # Empêche la réinitialisation du zoom lors des interactions
        mapbox=dict(
            zoom=6,  # Zoom initial
        )
    )
    
    return fig

# Lancer l'application
if __name__ == '__main__':
    app.run_server(debug=True)