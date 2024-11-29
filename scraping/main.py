import time
from scrapping_donnes_final_version import *
from JsonToBdd import *
from generate_random_address import *
from config_bdd import host, user, password, database

nb_points = 10
listes_points = find_addresses_within_radius("Genève", 50, nb_points)
insert_point_into_bdd(listes_points)
addresses_within_radius = listes_points[1]
i = 1

for address_data in addresses_within_radius:
    # Get longitude and latitude
    longitude = address_data[2]
    latitude = address_data[1]
    
    # Start the timer for the current iteration
    start_time = time.time()

    # Scrape the data and import it into MySQL
    json_données = scrapping(latitude, longitude)
    import_json_to_mysql(json_données)
    
    # End the timer and calculate the duration
    end_time = time.time()
    duration = end_time - start_time  # Time taken in seconds

    # Print the progress with the time taken for the current iteration
    print(f"Point {i}/{nb_points} effectué en {duration:.2f} secondes")
    
    # Increment the counter
    i += 1

# except :
#     ddb = mysql.connector.connect(
#    host=host,
#    user=user,
#    password=password,
#    database=database,
#    charset="utf8"  # Définir l'encodage en UTF-8
#)

#     with db.cursor() as c:
#         print("erreur ")
#         c.execute("CALL `delete_points_without_measure`();")

