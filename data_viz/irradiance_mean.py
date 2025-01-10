import dash
from dash import dcc, html
import plotly.express as px
import pandas as pd
import osmnx as ox
import geopandas as gpd

# Étape 1: Charger des bâtiments de Genève à partir d'OSM
def get_buildings_from_osm():
    # Charger les bâtiments dans une zone autour de Genève
    buildings = ox.features_from_place('Genève, Switzerland', tags={'building': True})
    
    # Convertir les géométries en un CRS projeté pour calculer le centroïde avec précision
    buildings = buildings.to_crs(epsg=3857)  # EPSG:3857 est une projection en mètres
    
    # Calculer le centroïde sur le CRS projeté
    buildings['centroid'] = buildings.geometry.centroid
    
    # Revenir à un CRS géographique pour obtenir les coordonnées lat/lon
    buildings = buildings.to_crs(epsg=4326)
    
    # Extraire les coordonnées des centroids
    buildings['lat'] = buildings['centroid'].y
    buildings['lon'] = buildings['centroid'].x
    
    # Retourner les bâtiments avec les coordonnées
    return buildings

# Charger les données de bâtiments
buildings = get_buildings_from_osm()

# Initialiser l'application Dash
app = dash.Dash(__name__)

# Créer la carte en utilisant Plotly Express avec seulement les centroides pour la sélection initiale
fig = px.scatter_mapbox(
    lat=buildings['lat'],
    lon=buildings['lon'],
    zoom=13,
    center={"lat": 46.2044, "lon": 6.1432},
    mapbox_style="open-street-map"
)

# Ajouter tous les polygones des bâtiments à la carte
for _, building in buildings.iterrows():
    geometry = building.geometry
    if geometry.geom_type == 'Polygon':
        lats, lons = geometry.exterior.xy
        fig.add_scattermapbox(
            lat=list(lats),
            lon=list(lons),
            mode='lines',
            fill='toself',
            line=dict(color='blue', width=2),
            name='Bâtiment'
        )
    elif geometry.geom_type == 'MultiPolygon':
        for poly in geometry.geoms:
            lats, lons = poly.exterior.xy
            fig.add_scattermapbox(
                lat=list(lats),
                lon=list(lons),
                mode='lines',
                fill='toself',
                line=dict(color='blue', width=2),
                name='Bâtiment'
            )

# Layout de l'application
app.layout = html.Div(children=[
    html.H1(children="Carte 2D Interactive des Bâtiments à Genève"),

    # Graphique de la carte 2D
    dcc.Graph(
        id='2d-map',
        figure=fig,
        style={'height': '80vh', 'width': '100%'}
    )
])

# Lancer l'application
if __name__ == '__main__':
    app.run_server(debug=True)