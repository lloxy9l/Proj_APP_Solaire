from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
import numpy as np
import pandas as pd

def predict_future_production(df):
    """
    Prédit la production solaire future (2035)
    à partir des données météo, en utilisant un modèle de machine learning.
    La production actuelle est conservée telle quelle depuis fetch_data().
    """

    # Copie du DataFrame pour éviter de le modifier directement
    df = df.copy()

    # === Vérification et nettoyage ===
    numeric_cols = ["irradiance", "temperature", "ensoleillement", "precipitation", "production"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=numeric_cols)

    # === Étape 1. Utilisation de la production actuelle existante ===
    df.rename(columns={"production": "production_actuelle"}, inplace=True)

    # === Étape 2. Préparation du modèle ===
    X = df[["irradiance", "temperature", "ensoleillement", "precipitation"]]
    y = df["production_actuelle"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestRegressor(
        n_estimators=300,
        max_depth=12,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train, y_train)
    score = model.score(X_test, y_test)
    print(f"📈 Précision du modèle IA sur la production actuelle : {score:.2%}")

    # === Étape 3. Simulation du climat futur (projection 2035) ===
    nb_annees = 10
    df_future = X.copy()
    df_future["irradiance"] = df["irradiance"] * (1 + 0.02 * nb_annees)      # +2%/an
    df_future["precipitation"] = df["precipitation"] * (1 - 0.005 * nb_annees) # -0.5%/an
    df_future["temperature"] = df["temperature"] + (0.3 * nb_annees)          # +0.3°C/an
    df_future["ensoleillement"] = df["ensoleillement"] * (1 + 0.01 * nb_annees) # +1%/an

    # === Étape 4. Prédiction de la production future ===
    df["production_2035"] = model.predict(df_future)

    # === Étape 5. Calcul de la variation ===
    df["variation_percent"] = (
        (df["production_2035"] - df["production_actuelle"]) / df["production_actuelle"]
    ) * 100

    # Nettoyage et arrondis
    df["production_actuelle"] = df["production_actuelle"].round(2)
    df["production_2035"] = df["production_2035"].round(2)
    df["variation_percent"] = df["variation_percent"].round(2)

    print("✅ Prédictions futures 2035 calculées avec le modèle IA.")
    return df
