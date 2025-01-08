import mysql.connector
import pandas as pd
from geopy.geocoders import Nominatim
import time

# Connexion à la base de données MySQL
def get_communes_from_db():
    conn = mysql.connector.connect(
        host='host',    # Adresse du serveur MySQL
        user='user',   # Nom d'utilisateur MySQL
        password='password',  # Mot de passe MySQL
        database='database'   # Nom de la base de données
    )
    
    # Récupérer les noms des communes sans géodonnées
    query = "SELECT nom_commune FROM 2026_solarx_consommation"
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    return df

# Connexion à la base de données MySQL pour insérer les coordonnées
def insert_geodata_to_db(commune, lat, lon):
    conn = mysql.connector.connect(
        host='host',    # Adresse du serveur MySQL
        user='user',   # Nom d'utilisateur MySQL
        password='password',  # Mot de passe MySQL
        database='database'   # Nom de la base de données
    )
    
    cursor = conn.cursor()

    # Insérer les coordonnées dans une nouvelle table dédiée
    insert_query = """
    INSERT INTO communes_geodata (nom_commune, latitude, longitude)
    VALUES (%s, %s, %s)
    ON DUPLICATE KEY UPDATE latitude=%s, longitude=%s
    """
    
    # Exécuter la requête d'insertion avec les coordonnées
    cursor.execute(insert_query, (commune, lat, lon, lat, lon))
    conn.commit()
    conn.close()

# Géocoder une commune à l'aide de Geopy (API OpenStreetMap)
def get_commune_coordinates(commune_name):
    geolocator = Nominatim(user_agent="geoapiExercises")
    try:
        location = geolocator.geocode(commune_name + ', France')
        if location:
            return location.latitude, location.longitude
        else:
            return None, None
    except Exception as e:
        print(f"Erreur de géocodage pour {commune_name}: {e}")
        return None, None

# Processus de géocodage des communes et insertion dans la base de données
def geocode_and_store_communes():
    # Étape 1 : Récupérer les communes
    communes_df = get_communes_from_db()

    # Étape 2 : Pour chaque commune, récupérer les coordonnées
    for index, row in communes_df.iterrows():
        commune_name = row['nom_commune']

        # Récupérer les coordonnées géographiques de la commune
        lat, lon = get_commune_coordinates(commune_name)
        
        if lat and lon:
            print(f"Géocodé : {commune_name} -> lat: {lat}, lon: {lon}")
            
            # Étape 3 : Stocker les coordonnées dans la base de données
            insert_geodata_to_db(commune_name, lat, lon)
        else:
            print(f"Coordonnées non trouvées pour {commune_name}")

        # Pause pour éviter de dépasser les limites de requêtes de l'API OpenStreetMap
        time.sleep(0.1)

if __name__ == '__main__':
    # Exécution du processus de géocodage et stockage des communes
    geocode_and_store_communes()