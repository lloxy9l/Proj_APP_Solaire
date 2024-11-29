from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import math 
import random
import sqlite3
import mysql.connector
from config_bdd import host, user, password, database

db = mysql.connector.connect(
    host=host,
    user=user,
    password=password,
    database=database,
    charset="utf8"  # Définir l'encodage en UTF-8
    )

def find_addresses_within_radius(central_address, radius_km, num_points):
    
    # Initialize Nominatim geocoder
    geolocator = Nominatim(user_agent="my_geocoder")

    # Geocode the central address
    central_location = geolocator.geocode(central_address)
   
    
    if central_location:
        central_point = (central_location.latitude, central_location.longitude)
        addresses_within_radius = []

        for _ in range(num_points):
            # Generate random coordinates within the radius
            u = random.random()
            v = random.random()
            
            radius_in_degrees = radius_km / 111.0
            
            w = radius_in_degrees * (u ** 0.5)
            t = 2 * 3.141592653589793 * v
            x = w * math.cos(t)
            y = w * math.sin(t)

            # Adjust coordinates to be within the circular area
            adjusted_latitude = central_point[0] + y
            adjusted_longitude = central_point[1] + x

            # Reverse geocode to get address
            address = geolocator.reverse((adjusted_latitude, adjusted_longitude))
            addresses_within_radius.append((address.address, round(adjusted_latitude,4), round(adjusted_longitude,4)))

        return [[central_location.address, central_location.longitude, central_location.latitude,radius_km],addresses_within_radius]
    else:
        return None

def insert_point_into_bdd(data):
    central_address = data[0][0]
    longitude_zone = data[0][1]
    latitude_zone = data[0][2]
    addresses_within_radius = data[1]
    radius_km = data[0][3]

    with db.cursor() as c:
        # Insert into Zone table
        c.execute(
            "INSERT IGNORE INTO 2026_solarx_Zone (nom, rayon, origin_latitude, origin_longitude) VALUES (%s, %s, %s, %s)",
            (central_address, radius_km, latitude_zone, longitude_zone),
        )
        db.commit()

        # Fetch idzone for the Zone entry
        c.execute("SELECT idzone FROM 2026_solarx_Zone WHERE nom LIKE %s", (central_address,))
        idzone_result = c.fetchall()
        if idzone_result:
            idzone = idzone_result[0]
        else:
            raise Exception(f"Zone {central_address} not found after insertion.")
        
        # Close the cursor after fetching results
        c.close()

    with db.cursor() as c:
        # Insert points into pointsgps and associate them with the Zone
        for address_data in addresses_within_radius:
            longitude = address_data[2]
            latitude = address_data[1]
            address = address_data[0]

            # Insert into pointsgps
            c.execute(
                "INSERT INTO 2026_solarx_pointsgps (latitude, longitude, adresse) VALUES (%s, %s, %s)",
                (latitude, longitude, address),
            )
            db.commit()

            # Fetch idpoint for the newly inserted point
            c.execute(
                "SELECT idpoint FROM 2026_solarx_pointsgps WHERE adresse = %s",
                (address,),
            )
          
            id_point_result = c.fetchall()

            if id_point_result:
                id_point = id_point_result[0]
            else:
                raise Exception(
                    f"Point with latitude {latitude} and longitude {longitude} not found after insertion."
                )

            id_point = id_point[0] if isinstance(id_point, tuple) else id_point
            idzone = idzone[0] if isinstance(idzone, tuple) else idzone

            # Insert into appartient table
            c.execute(
                "INSERT INTO 2026_solarx_appartient (idpoint, idzone) VALUES (%s, %s)",
                (id_point, idzone),
            )
            db.commit()

    print("Points successfully inserted into the database")
