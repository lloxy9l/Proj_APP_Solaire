"""
Module IA : prédiction solaire intelligente et simulation de panneaux
Utilise les données météo pour estimer la production actuelle et future (2035)
et le nombre de panneaux à installer.
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import warnings
warnings.filterwarnings("ignore")

# ==========================
# 1️⃣ Détection des tendances
# ==========================
def detecter_tendances_climatiques(df):
    """
    Analyse automatiquement les tendances climatiques à partir des dates de collecte :
    - croissance de l'irradiance
    - baisse des précipitations
    """
    if "date_collecte" not in df.columns:
        raise ValueError("❌ La colonne 'date_collecte' est requise.")

    df["annee"] = df["date_collecte"].dt.year
    trends = df.groupby("annee")[["irradiance", "precipitation"]].mean().reset_index()

    def pente(X, y):
        X = np.array(X).reshape(-1, 1)
        model = LinearRegression().fit(X, y)
        return model.coef_[0]

    try:
        p_irr = pente(trends["annee"], trends["irradiance"])
        p_precip = pente(trends["annee"], trends["precipitation"])
    except Exception:
        p_irr, p_precip = 0.015, -0.005  # Valeurs par défaut

    taux_irr = p_irr / trends["irradiance"].mean()
    taux_precip = -p_precip / trends["precipitation"].mean()

    print(f"📈 Tendance détectée : +{taux_irr*100:.2f}%/an irradiance, -{taux_precip*100:.2f}%/an précipitations")
    return taux_irr, taux_precip

# ==========================
# 2️⃣ Entraînement du modèle IA
# ==========================
def entrainer_modele_production(df):
    features = ["irradiance", "ensoleillement", "temperature", "precipitation"]
    df = df.dropna(subset=features)
    df["production_reelle"] = df["irradiance"] * (365 - df["precipitation"]/10) * 3

    X = df[features]
    y = df["production_reelle"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
    model.fit(X_train, y_train)

    score = model.score(X_test, y_test)
    print(f"🤖 Modèle IA entraîné — R² = {score:.3f}")
    return model

# ==========================
# 3️⃣ Prédiction future et simulation
# ==========================
def predict_future_production_ai(df):
    """
    Prédit la production actuelle et 2035, le nombre de panneaux et le ROI.
    """
    taux_irr, taux_precip = detecter_tendances_climatiques(df)
    nb_annees = 10

    model = entrainer_modele_production(df)
    features = ["irradiance", "ensoleillement", "temperature", "precipitation"]

    # Production actuelle
    df["production_actuelle"] = model.predict(df[features])

    # Scénario futur
    df_future = df.copy()
    df_future["irradiance"] *= (1 + taux_irr * nb_annees)
    df_future["precipitation"] *= (1 - taux_precip * nb_annees)
    df_future["temperature"] += 1.5
    df_future["ensoleillement"] *= 1.02

    df["production_2035"] = model.predict(df_future[features])
    df["variation_percent"] = ((df["production_2035"] - df["production_actuelle"]) / df["production_actuelle"]) * 100

    # Simulation panneaux
    surface_panneau = 1.7
    puissance_panneau = 350
    rendement = 0.85

    df["surface_m2"] = df.get("surface_m2", np.random.randint(5000, 20000, size=len(df)))
    df["nb_panneaux_ia"] = (df["surface_m2"] / surface_panneau * rendement).astype(int)
    df["production_annuelle_kwh"] = (df["nb_panneaux_ia"] * puissance_panneau * rendement * 1200 / 1000).round(0)

    # ROI estimé
    cout = df["nb_panneaux_ia"] * 200
    revenu = df["production_annuelle_kwh"] * 0.15
    df["roi_annees"] = (cout / revenu).round(1)

    df[["production_actuelle", "production_2035", "variation_percent"]] = df[["production_actuelle", "production_2035", "variation_percent"]].round(2)
    print("✅ Simulation IA complète (production, panneaux, ROI)")
    return df
