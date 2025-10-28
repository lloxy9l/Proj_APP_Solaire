import pandas as pd

def generate_sql_for_csv(csv_path):
    # Lire le fichier CSV
    df = pd.read_csv(csv_path,index_col=False)
    
    # Créer les requêtes SQL
    sql_points = []
    sql_mesures = []
    id_point_current = 773  # ID de départ pour les points GPS
    print("Colonnes du CSV :", df.columns)
    print(df.head())
    # Parcourir chaque ligne pour générer les requêtes
    for i, row in df.iterrows():
        # Insertion dans la table 2026_solarx_pointsgps (correctement inversée latitude et longitude)
        point_sql = f"INSERT INTO 2026_solarx_pointsgps (latitude, longitude, adresse) VALUES ({row['latitude']}, {row['longitude']}, 'None');"
        sql_points.append(point_sql)
        
        # Insertion dans la table 2026_solarx_mesures
        mesure_sql = f"INSERT INTO 2026_solarx_mesures (temperature, ensoleillement, irradiance, precipitation, date_collecte, idpoint) " \
                     f"VALUES ({row['temperature_predite']}, {row['ensoleillement_predite']}, {row['irradiance_predite']}, " \
                     f"{row['precipitation_predite']}, '2020-01-01 00:00:00', {id_point_current});"
        sql_mesures.append(mesure_sql)
        
        # Incrémentation de l'ID pour le prochain point
        id_point_current += 1
    
    # Sauvegarder les requêtes SQL dans un fichier
    sql_output = '\n'.join(sql_points + sql_mesures)
    
    # Sauvegarde du fichier SQL
    output_file_path = csv_path.replace(".csv", "_insertion_data.sql")
    with open(output_file_path, 'w') as f:
        f.write(sql_output)
    
    print(f"Le fichier SQL a été généré : {output_file_path}")

# Exemple d'utilisation
csv_path = 'points_combines.csv'  # Remplacer par le chemin de votre fichier CSV
generate_sql_for_csv(csv_path)
