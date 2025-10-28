"""
Module d'extraction et d'analyse des zones industrielles
pour l'installation de panneaux solaires.
VERSION MODIFIÉE : Recherche dans un RAYON autour de la ville (inclut les communes voisines)
"""

import os
import json
import warnings
warnings.filterwarnings('ignore')

import osmnx as ox
import geopandas as gpd
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split


# =====================================================
# FONCTION PRINCIPALE D'INITIALISATION
# =====================================================
def initialize_default_data():
    """
    Initialise automatiquement les données au démarrage du dashboard.
    Si le fichier JSON n'existe pas, il est créé pour Genève + communes voisines.
    """
    json_path = "assets/maps/zones_industrielles.json"
    if not os.path.exists(json_path):
        print("⚙️ Initialisation : génération des données pour Genève + environs...")
        # CHANGEMENT ICI : rayon de 20km pour inclure les communes voisines
        df = extract_industrial_zones("Geneva, Switzerland", radius_km=20)
        if df is not None:
            df = get_zones_dataframe(df)
            df["ville"] = "Geneva, Switzerland"
            os.makedirs("assets/maps", exist_ok=True)
            df.to_json(json_path, orient="records", force_ascii=False)
            print("✅ Données initiales créées pour Genève + environs.")
        else:
            print("⚠️ Impossible de générer les données initiales.")
    else:
        print("✅ Données industrielles déjà présentes.")


# =====================================================
# EXTRACTION DES ZONES INDUSTRIELLES - VERSION RAYON
# =====================================================
def extract_industrial_zones(zone="Geneva, Switzerland", radius_km=20, use_cache=True):
    """
    Extrait les zones industrielles dans un RAYON autour de la ville.
    
    CHANGEMENT PRINCIPAL : Au lieu de chercher QUE dans la ville,
    on cherche dans un rayon de X km autour du centre de la ville.
    
    Args:
        zone: Nom de la ville
        radius_km: Rayon en km (20km = toute l'agglomération genevoise)
    """
    try:
        print(f"🔍 Extraction des zones industrielles pour {zone}...")
        print(f"   📍 Recherche dans un rayon de {radius_km} km (inclut les communes voisines)")
        
        # ÉTAPE 1 : Trouver le centre de la ville
        location = ox.geocode(zone)  # Retourne (latitude, longitude)
        print(f"   🎯 Centre trouvé : {location[0]:.4f}, {location[1]:.4f}")
        
        # ÉTAPE 2 : Chercher dans un RAYON autour du centre (pas juste dans la ville)
        tags = {"landuse": "industrial"}
        gdf = ox.features_from_point(
            location,                    # Point central
            tags=tags,                   # Ce qu'on cherche
            dist=radius_km * 1000        # Distance en MÈTRES (20km = 20000m)
        )

        if gdf.empty:
            print("⚠️ Aucune zone industrielle trouvée.")
            return None

        print(f"   ✅ {len(gdf)} zones trouvées (Geneva + Vernier + Meyrin + Carouge + etc.)")

        # ÉTAPE 3 : Calcul des surfaces et coordonnées
        gdf = gdf.reset_index()
        gdf = gdf.to_crs(epsg=2056)  # Projection suisse pour calcul surface
        gdf["surface_m2"] = gdf.geometry.area
        gdf["centroid_x"] = gdf.geometry.centroid.x
        gdf["centroid_y"] = gdf.geometry.centroid.y

        gdf = gdf.to_crs(epsg=4326)  # Retour en GPS
        gdf["latitude"] = gdf.geometry.centroid.y
        gdf["longitude"] = gdf.geometry.centroid.x

        # ÉTAPE 4 : Modèle ML et production
        gdf = train_adaptability_model(gdf)
        gdf["production_potentielle_kwh"] = gdf["surface_m2"] * 0.15 * 150

        print(f"✅ {len(gdf)} zones trouvées dans {radius_km}km autour de {zone}.")
        return gdf

    except Exception as e:
        print(f"❌ Erreur lors de l'extraction : {e}")
        return None


# =====================================================
# ENTRAÎNEMENT DU MODÈLE ML
# =====================================================
def train_adaptability_model(gdf):
    surface_thr = gdf["surface_m2"].median()
    gdf["label_adapte"] = (
        (gdf["surface_m2"] > surface_thr) &
        (gdf["centroid_x"] > gdf["centroid_x"].mean())
    ).astype(int)

    if len(gdf) >= 10:
        features = gdf[["surface_m2", "centroid_x", "centroid_y"]].values
        labels = gdf["label_adapte"].values
        test_size = min(0.3, max(0.1, 3 / len(labels)))

        clf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
        X_train, X_test, y_train, y_test = train_test_split(features, labels, test_size=test_size, random_state=42)
        clf.fit(X_train, y_train)
        gdf["prediction_adapte"] = clf.predict(features)
        print(f"📊 Précision du modèle : {clf.score(X_test, y_test):.2%}")
    else:
        gdf["prediction_adapte"] = (gdf["surface_m2"] > gdf["surface_m2"].median()).astype(int)
        print("⚠️ Peu de données, classification simplifiée.")

    seuil_bas, seuil_haut = 5000, 10000
    def categorize(row):
        if row["prediction_adapte"] == 1 and row["surface_m2"] > seuil_haut:
            return "Adaptée"
        elif seuil_bas <= row["surface_m2"] < seuil_haut:
            return "Moyenne"
        else:
            return "Non adaptée"

    gdf["niveau_adaptabilite"] = gdf.apply(categorize, axis=1)
    return gdf


# =====================================================
# CONVERSION POUR DASH / JSON
# =====================================================
def get_zones_dataframe(gdf):
    return pd.DataFrame({
        'latitude': gdf['latitude'],
        'longitude': gdf['longitude'],
        'surface_m2': gdf['surface_m2'],
        'niveau_adaptabilite': gdf['niveau_adaptabilite'],
        'production_potentielle': gdf['production_potentielle_kwh'] / 1000,
        'name': gdf.get('name', [f'Zone {i+1}' for i in range(len(gdf))])
    })


# =====================================================
# RECHERCHE DYNAMIQUE DE NOUVELLE RÉGION
# =====================================================
def search_new_region(region_name, radius_km=20):
    """
    Recherche et exporte les zones d'une nouvelle région + ses environs.
    
    Args:
        region_name: Nom de la ville
        radius_km: Rayon de recherche (défaut 20km)
    """
    print(f"\n🔎 Recherche et extraction pour {region_name} + {radius_km}km autour...")
    df = extract_industrial_zones(region_name, radius_km=radius_km)
    if df is not None:
        df = get_zones_dataframe(df)
        df["ville"] = region_name
        os.makedirs("assets/maps", exist_ok=True)
        df.to_json("assets/maps/zones_industrielles.json", orient="records", force_ascii=False)
        print(f"✅ Données mises à jour pour {region_name} + environs")
    else:
        print("⚠️ Aucune donnée trouvée pour cette région.")