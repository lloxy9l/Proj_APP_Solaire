import overpy
import geojson

# Initialiser Overpass API
api = overpy.Overpass()

# Requête pour les communes de la Haute-Savoie et du canton de Genève
query = """
[out:json];
(
  area["name"="Haute-Savoie"]->.searchArea;
  relation["admin_level"="8"](area.searchArea);
  area["name"="Canton of Geneva"]->.searchAreaGeneve;
  relation["admin_level"="8"](area.searchAreaGeneve);
);
out body;
>;
out skel qt;
"""

try:
    # Exécuter la requête Overpass
    print("Exécution de la requête Overpass...")
    result = api.query(query)
    print("Requête terminée.")
except Exception as e:
    print(f"Erreur lors de la requête Overpass : {e}")
    exit()

# Convertir les relations en GeoJSON
features = []
for relation in result.relations:
    
    coords = []
    for way in relation.members:
        if way.role == "outer":
            try:
                coords.append(
                    [[float(node.lon), float(node.lat)] for node in way.resolve().nodes]
                )
            except Exception as e:
                print(f"Erreur lors de la résolution d'un chemin : {e}")
                continue

    if coords:
        # Ajouter une feature GeoJSON
        features.append(
            geojson.Feature(
                geometry=geojson.MultiPolygon([coords]),
                properties={"name": relation.tags.get("name", "Inconnu")}
            )
        )

if not features:
    print("Aucune donnée valide à sauvegarder. Vérifiez les résultats de la requête.")
    exit()

geojson_data = geojson.FeatureCollection(features)

# Sauvegarde en fichier GeoJSON
output_file = "communes_haute_savoie_geneve.geojson"
try:
    with open(output_file, "w", encoding="utf-8") as f:
        geojson.dump(geojson_data, f)
    print(f"Données GeoJSON sauvegardées dans {output_file}.")
except Exception as e:
    print(f"Erreur lors de la sauvegarde du fichier GeoJSON : {e}")
