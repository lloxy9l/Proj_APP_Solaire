import osmnx as ox
import pandas as pd
import os

path_to_file = "scraping/data/building_centroids.csv"

# Étape 1: Charger les bâtiments depuis OSM et calculer les centroïdes
def get_buildings_from_osm():
    # Charger uniquement les bâtiments dans une zone autour de Genève
    buildings = ox.features_from_place('Genève, Switzerland', tags={'building': True})
    
    # Convertir les géométries en un CRS projeté pour calculer les centroïdes avec précision
    buildings = buildings.to_crs(epsg=3857)  # EPSG:3857 est une projection en mètres
    
    # Calculer le centroïde de chaque bâtiment
    buildings['centroid'] = buildings.geometry.centroid
    
    # Revenir à un CRS géographique pour obtenir les coordonnées lat/lon
    buildings = buildings.to_crs(epsg=4326)
    
    # Extraire uniquement les colonnes d'intérêt (lat, lon, adresse si disponible)
    buildings['lat'] = buildings['centroid'].y
    buildings['lon'] = buildings['centroid'].x
    
    # Garder uniquement les colonnes liées aux coordonnées et à l'adresse
    columns_to_keep = ['lat', 'lon', 'addr:street', 'addr:housenumber', 'addr:postcode', 'addr:city']
    buildings = buildings[columns_to_keep]
    
    # Retourner les bâtiments avec uniquement les informations nécessaires
    return buildings

# Étape 2: Sauvegarder les centroïdes des bâtiments dans un fichier CSV
def save_buildings_to_csv(buildings, path):
    # Créer le répertoire s'il n'existe pas
    directory = os.path.dirname(path)
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    # Sauvegarder les données dans un fichier CSV
    buildings.to_csv(path, index=False)

# Étape 3: Charger les bâtiments depuis un fichier CSV
def load_buildings_from_csv(path):
    buildings = pd.read_csv(path)
    return buildings

# Charger les données de bâtiments depuis OSM ou depuis un fichier CSV
if not os.path.exists(path_to_file):
    buildings = get_buildings_from_osm()
    save_buildings_to_csv(buildings, path_to_file)
else:
    buildings = load_buildings_from_csv(path_to_file)

# Afficher quelques données pour vérification
print(buildings.head())