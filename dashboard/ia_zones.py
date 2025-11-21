"""
Module d'extraction et d'analyse des zones industrielles
pour l'installation de panneaux solaires
"""
import osmnx as ox
import geopandas as gpd
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import warnings
warnings.filterwarnings('ignore')


def extract_industrial_zones(zone="Geneva, Switzerland", use_cache=True):
    """
    Extrait les zones industrielles et calcule leur adaptabilité
    pour l'installation de panneaux solaires.
    
    Args:
        zone (str): Nom de la zone géographique à analyser
        use_cache (bool): Utiliser le cache d'OSMnx
    
    Returns:
        pd.DataFrame: DataFrame avec les zones et leur adaptabilité
        None: Si aucune donnée n'est trouvée
    """
    try:
        print(f"🔍 Extraction des zones industrielles pour {zone}...")
        
        # Extraction des zones industrielles via OpenStreetMap
        tags = {"landuse": "industrial"}
        gdf = ox.features_from_place(zone, tags=tags)
        
        if gdf.empty:
            print("⚠️ Aucune zone industrielle trouvée.")
            return None
        
        # Reset MultiIndex pour simplifier
        gdf = gdf.reset_index()
        
        # Projection suisse (CH1903+ / LV95) pour calculs précis
        gdf = gdf.to_crs(epsg=2056)
        gdf["surface_m2"] = gdf.geometry.area
        gdf["centroid_x"] = gdf.geometry.centroid.x
        gdf["centroid_y"] = gdf.geometry.centroid.y
        
        # Reprojection WGS84 pour affichage web
        gdf = gdf.to_crs(epsg=4326)
        gdf["latitude"] = gdf.geometry.centroid.y
        gdf["longitude"] = gdf.geometry.centroid.x
        
        # Entraînement du modèle d'adaptabilité
        gdf = train_adaptability_model(gdf)
        
        # Calcul du potentiel de production solaire
        # Hypothèse : 15% du toit utilisable, rendement 1000 kWh/kWp/an
        gdf["production_potentielle_kwh"] = gdf["surface_m2"] * 0.15 * 150
        
        print(f"✅ {len(gdf)} zones trouvées")
        print(f"✅ Zones adaptées : {(gdf['niveau_adaptabilite'] == 'Adaptée').sum()}")
        
        return gdf
        
    except Exception as e:
        print(f"❌ Erreur lors de l'extraction : {e}")
        return None


def train_adaptability_model(gdf):
    """
    Entraîne un modèle ML pour prédire l'adaptabilité des zones
    
    Args:
        gdf (GeoDataFrame): GeoDataFrame avec les zones
    
    Returns:
        GeoDataFrame: GeoDataFrame enrichi avec prédictions
    """
    # Génération de labels (critère simple : surface + position)
    surface_thr = gdf["surface_m2"].median()
    gdf["label_adapte"] = (
        (gdf["surface_m2"] > surface_thr) & 
        (gdf["centroid_x"] > gdf["centroid_x"].mean())
    ).astype(int)
    
    # Entraînement seulement si assez de données
    if len(gdf) >= 10:
        features = gdf[["surface_m2", "centroid_x", "centroid_y"]].values
        labels = gdf["label_adapte"].values
        
        # Validation croisée
        test_size = min(0.3, max(0.1, 3 / len(labels)))
        X_train, X_test, y_train, y_test = train_test_split(
            features, labels, test_size=test_size, random_state=42
        )
        
        # Random Forest optimisé
        clf = RandomForestClassifier(
            n_estimators=100, 
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        clf.fit(X_train, y_train)
        
        # Prédiction sur toutes les zones
        gdf["prediction_adapte"] = clf.predict(features)
        
        # Score du modèle
        score = clf.score(X_test, y_test)
        print(f"📊 Précision du modèle : {score:.2%}")
    else:
        # Fallback simple si peu de données
        gdf["prediction_adapte"] = (
            gdf["surface_m2"] > gdf["surface_m2"].median()
        ).astype(int)
        print("⚠️ Peu de données, classification simplifiée")
    
    # Classification en 3 niveaux
    seuil_bas = 5000   # m²
    seuil_haut = 10000 # m²
    
    def categorize_adaptability(row):
        if row["prediction_adapte"] == 1 and row["surface_m2"] > seuil_haut:
            return "Adaptée"
        elif row["surface_m2"] >= seuil_bas and row["surface_m2"] < seuil_haut:
            return "Moyenne"
        else:
            return "Non adaptée"
    
    gdf["niveau_adaptabilite"] = gdf.apply(categorize_adaptability, axis=1)
    
    return gdf


def get_zones_dataframe(gdf):
    """
    Convertit le GeoDataFrame en DataFrame Pandas simple pour Dash
    
    Args:
        gdf (GeoDataFrame): GeoDataFrame des zones
    
    Returns:
        pd.DataFrame: DataFrame simplifié
    """
    if gdf is None:
        return create_fallback_data()
    
    return pd.DataFrame({
        'latitude': gdf['latitude'],
        'longitude': gdf['longitude'],
        'surface_m2': gdf['surface_m2'],
        'niveau_adaptabilite': gdf['niveau_adaptabilite'],
        'production_potentielle': gdf['production_potentielle_kwh'] / 1000,  # En MWh
        'name': gdf.get('name', [f'Zone {i+1}' for i in range(len(gdf))])
    })


def create_fallback_data():
    """
    Crée des données de secours si l'extraction échoue
    
    Returns:
        pd.DataFrame: Données factices pour tests
    """
    print("⚠️ Utilisation de données de secours")
    return pd.DataFrame({
        'latitude': [46.2044, 46.2100, 46.1990],
        'longitude': [6.1432, 6.1500, 6.1350],
        'surface_m2': [12000, 8500, 15000],
        'niveau_adaptabilite': ['Adaptée', 'Moyenne', 'Adaptée'],
        'production_potentielle': [1800, 1275, 2250],
        'name': ['Zone Industrielle A', 'Zone Industrielle B', 'Zone Industrielle C']
    })


# Point d'entrée principal
if __name__ == "__main__":
    # Test du module
    zones = extract_industrial_zones()
    if zones is not None:
        df = get_zones_dataframe(zones)
        print("\n📋 Aperçu des données :")
        print(df.head())
        print(f"\n📊 Statistiques :")
        print(df['niveau_adaptabilite'].value_counts())