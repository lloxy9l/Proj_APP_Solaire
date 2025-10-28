# Pipeline IA : Extraction, génération de features, entraînement, prédiction
# pip install osmnx geopandas pandas scikit-learn

import osmnx as ox
import geopandas as gpd
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

# 1. Extraction des zones industrielles à Genève
ZONE = "Geneva, Switzerland"
print(f"Extraction des zones industrielles pour {ZONE}...")
tags = {"landuse": "industrial"}
gdf = ox.features_from_place(ZONE, tags=tags)

if gdf.empty:
    print("Aucune zone industrielle trouvée.")
    exit()

# Reset MultiIndex to make 'osmid' and 'element_type' columns
gdf = gdf.reset_index()

# 2. Génération de features (surface, centroides, etc.)
gdf = gdf.to_crs(epsg=2056)  # Projection suisse pour surface
gdf["surface_m2"] = gdf.geometry.area
gdf["centroid_x"] = gdf.geometry.centroid.x
gdf["centroid_y"] = gdf.geometry.centroid.y

# Debugging: Print available columns to verify 'osmid'
print("Colonnes disponibles dans gdf:", gdf.columns.tolist())

# 3. Génération de labels fictifs (pour l'exemple)
# Ajuster le seuil pour équilibrer les classes
surface_thr = gdf["surface_m2"].median()  # Use median to balance
gdf["label_adapte"] = ((gdf["surface_m2"] > surface_thr) & 
                       (gdf["centroid_x"] > gdf["centroid_x"].mean())).astype(int)

# Vérifier la répartition des labels
print("Répartition des labels:", gdf["label_adapte"].value_counts())

# 4. Préparation du dataset IA
features = gdf[["surface_m2", "centroid_x", "centroid_y"]].values
labels = gdf["label_adapte"].values

# Vérifier la taille du dataset
if len(labels) < 10:
    print("Attention : Dataset trop petit pour un entraînement fiable. Considérez d'ajouter plus de données.")
    exit()

# Ajuster test_size pour petits datasets
test_size = min(0.3, 1.0 / len(labels)) if len(labels) > 1 else 0.3
X_train, X_test, y_train, y_test = train_test_split(features, labels, test_size=test_size, random_state=42)

# 5. Entraînement du modèle IA
clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X_train, y_train)

# 6. Prédiction sur toutes les zones
gdf["prediction_adapte"] = clf.predict(gdf[["surface_m2", "centroid_x", "centroid_y"]].values)

# 7. Affichage des résultats
print("\nRapport de classification sur le test :")
y_pred = clf.predict(X_test)
print(classification_report(y_test, y_pred, zero_division=0))

# Définir les seuils pour "moyenne"
seuil_bas = 5000
seuil_haut = 10000

# Ajout de la colonne niveau_adaptabilite
def get_niveau(row):
    if row["prediction_adapte"] == 1:
        return "Adaptée"
    elif row["surface_m2"] >= seuil_bas and row["surface_m2"] < seuil_haut:
        return "Moyenne"
    else:
        return "Non adaptée"
gdf["niveau_adaptabilite"] = gdf.apply(get_niveau, axis=1)

# Affichage de toutes les zones
print("\nListe des zones industrielles et leur adaptabilité :")
cols_to_show = [col for col in ["name", "surface_m2", "niveau_adaptabilite"] if col in gdf.columns]
print(gdf[cols_to_show].to_string(index=False))

# 8. Sauvegarde des résultats
# Vérifier que les colonnes nécessaires existent
required_cols = ["geometry", "surface_m2", "prediction_adapte"]
if "osmid" in gdf.columns:
    required_cols.append("osmid")
else:
    print("Colonne 'osmid' non trouvée, sauvegarde sans 'osmid'.")

try:
    gdf[required_cols].to_file("zones_industrielles_ai.geojson", driver="GeoJSON")
    gdf[required_cols].to_csv("zones_industrielles_ai.csv", index=False)
    print("\nFichiers générés : zones_industrielles_ai.geojson, zones_industrielles_ai.csv")
except Exception as e:
    print(f"Erreur lors de la sauvegarde : {e}")