import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from geopy.distance import geodesic
from tqdm import tqdm
import plotly.express as px
import pandas as pd
import numpy as np
from geopy.distance import geodesic
from tqdm import tqdm
import random

# === 1. Charger les fichiers CSV ===
df_points = pd.read_csv('2026_solarx_pointsgps.csv')  # idpoint, latitude, longitude, adresse
df_mesures = pd.read_csv('2026_solarx_mesures.csv')   # id, temperature, ensoleillement, irradiance, precipitation, date_collecte, idpoint

# Joindre les données
df = pd.merge(df_mesures, df_points, on='idpoint')

# === 2. Création de nouvelles zones à partir des points existants ===
rayon_exclusion_km = 0.5  # Minimum 500m d’écart avec les points existants

existing_coords = df_points[['latitude', 'longitude']].drop_duplicates().values

# Paramètres du Poisson Disk Sampling
min_dist_km = 0.5  # Rayon minimal entre les points
max_attempts = 1000  # Nombre maximal d'essais pour chaque tentative de génération de point

# === 3. Générer des nouveaux points en dehors de la zone des anciens ===
def poisson_disk_sampling(existing_coords, min_dist_km, max_attempts=1000):
    new_points = []
    min_lat, max_lat = 46.12388, 46.2535
    min_lon, max_lon = 5.98169,6.32715
    i=0
    while len(new_points) < 300:  # On veut générer un nombre de nouveaux points
        # Choisir un point de départ aléatoire
        lat = random.uniform(min_lat, max_lat)
        lon = random.uniform(min_lon, max_lon)
        coord = (lat, lon)
        
        # Vérifier si ce point est trop proche de ceux existants
        too_close = any(geodesic(coord, (e_lat, e_lon)).km < min_dist_km for e_lat, e_lon in existing_coords)
        
        # Si le point n'est pas trop proche, on l'ajoute
        if not too_close:
            i+=1
            new_points.append(coord)
            print("point ",i,"/400")
        # Limiter les tentatives de génération de points (éviter une boucle infinie)
        if len(new_points) >= max_attempts:
            break

    return new_points

# Générer les nouveaux points
nouveaux_points = poisson_disk_sampling(existing_coords, rayon_exclusion_km)

# Convertir en DataFrame
df_new = pd.DataFrame(nouveaux_points, columns=['latitude', 'longitude'])
print(f"✅ {len(df_new)} nouveaux points générés.")

# === 4. Prédire les variables météo pour ces nouveaux points ===
variables = ['temperature', 'ensoleillement', 'irradiance', 'precipitation']
df_mean = df.groupby(['idpoint', 'latitude', 'longitude'])[variables].mean().reset_index()

# Prédire pour chaque variable
X_train = df_mean[['latitude', 'longitude']]
for var in tqdm(variables, desc="Prédictions météo"):
    y_train = df_mean[var]
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    df_new[f"{var}_predite"] = model.predict(df_new[['latitude', 'longitude']])

# === 5. Fusionner anciens et nouveaux points ===
# Renommer les colonnes des anciens points
df_mean_renamed = df_mean.rename(columns={
    'temperature': 'temperature_predite',
    'ensoleillement': 'ensoleillement_predite',
    'irradiance': 'irradiance_predite',
    'precipitation': 'precipitation_predite'
})
df_mean_renamed = df_mean_renamed[['latitude', 'longitude'] + [f"{v}_predite" for v in variables]]

# Ajouter une colonne "source"
df_mean_renamed['source'] = 'existant'
df_new['source'] = 'prédit'

# Fusionner les deux
df_new.to_csv('points_nouveau.csv', index=False)
print(f"✅ Fichier final avec tous les points enregistré : points_combines.csv")
df_ancien = pd.read_csv('points_combines.csv')   # id, temperature, ensoleillement, irradiance, precipitation, date_collecte, idpoint
df_all = pd.concat([df_ancien, df_new], ignore_index=True)
# === 6. Visualisation sur la carte avec Plotly ===
fig = px.scatter_mapbox(
    df_all,
    lat="latitude",
    lon="longitude",
    color="temperature_predite",
    color_continuous_scale="Plasma",
    size=[200] * len(df_all),
    hover_data={
        "latitude": True,
        "longitude": True,
        "source": True,
        "temperature_predite": True,
        "ensoleillement_predite": True,
        "irradiance_predite": True,
        "precipitation_predite": True,
    },
    title="Température prédite en °C - Carte interactive",
    mapbox_style="carto-positron",
    center={"lat": 46.2047, "lon": 6.14231},  # Centré sur Genève
    zoom=8,
)

fig.update_layout(
    title={
        "text": "Température quotidienne (existants + prédits)",
        "font": {"size": 26},
        "x": 0.5,
    },
    margin={"r":0,"t":50,"l":0,"b":0},
    height=700,
)

fig.show()
