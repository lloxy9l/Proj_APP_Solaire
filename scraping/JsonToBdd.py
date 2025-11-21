#@author maxens soldan

# Exemple de fichier JSON : 

#{
#  "nom_de_la_table_a_ajouter": [
#    {
#      "ville": "Paris",
#      "temperature": 20,
#      "ensoleillement": "partiellement nuageux",
#      "taux_humidite": 60,
#      "production_solaire": 3500
#    },
#    Autres entrées de données...
#  ]
#}

from config_bdd import host, user, password, database
import mysql.connector
import json

def select_table_name_from_database(cursor):
    cursor.execute("SHOW TABLES")
    tables = [table[0] for table in cursor.fetchall()]
    print("Tables disponibles dans la base de données :")
    for index, table in enumerate(tables):
        print(f"{index + 1}. {table}")
    while True:
        table_index = input("Choisissez le numéro de la table à utiliser : ")
        try:
            table_index = int(table_index)
            if 1 <= table_index <= len(tables):
                return tables[table_index - 1]
            else:
                print("Numéro de table invalide. Veuillez choisir un numéro de table valide.")
        except ValueError:
            print("Veuillez entrer un numéro valide.")

def import_json_to_mysql(data):
    # # Créer une fenêtre Tkinter pour choisir le fichier
    # root = tk.Tk()
    # root.withdraw()  # Masquer la fenêtre principale

    # # Demander à l'utilisateur de choisir un fichier JSON
    # json_file_path = filedialog.askopenfilename(title="Choisir un fichier JSON", filetypes=(("Fichiers JSON", "*.json"), ("Tous les fichiers", "*.*")))

    # if not json_file_path:
    #     print("Aucun fichier sélectionné. Sortie du programme.")
    #     return

    # Connexion à la base de données MySQL
    db = mysql.connector.connect(
    host=host,
    user=user,
    password=password,
    database=database,
    charset="utf8"  # Définir l'encodage en UTF-8
    )

    # # Ouverture du fichier JSON avec l'encodage UTF-8
    # with open(json_file_path, 'r', encoding='utf-8') as f:
    #     data = json.load(f)

    # Récupération du nom de la table parmi les tables existantes dans la base de données
    with db.cursor() as c:
        table_name = "mesures"
        rows = data[table_name]


        # Insertion des données dans la table
        for row in rows:
            columns = ", ".join(row.keys())
            placeholders = ", ".join(["%s"] * len(row.values()))  # Création des placeholders pour les valeurs
            values = tuple(row.values())  # Convertir les valeurs en tuple
            insert_query = f"INSERT INTO 2026_solarx_{table_name} ({columns}) VALUES ({placeholders})"
            try:
                c.execute(insert_query, values)  # Passer les valeurs directement à la méthode execute()
            except:
                db = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database,
                charset="utf8"  # Définir l'encodage en UTF-8
                )
                c.execute(insert_query, values)  # Passer les valeurs directement à la méthode execute()
    

    # Valider et appliquer les modifications dans la base de données
    db.commit()
    print("données météo insérées dans la bdd")
    # Fermer la connexion à la base de données
    db.close()

if __name__ == "__main__":
    import_json_to_mysql()
