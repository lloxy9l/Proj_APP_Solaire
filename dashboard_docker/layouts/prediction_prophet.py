import pandas as pd
import mysql.connector
from prophet import Prophet
from datetime import datetime, timedelta
import os
import warnings
warnings.filterwarnings('ignore')

# Configuration BDD
host = os.environ.get("DB_HOST", "db")
user = "root"
password = "rootpassword"
database = "projet_solarx"

# Flag global pour arrêter les prédictions
STOP_PREDICTION_FLAG = False

def set_stop_flag(value=True):
    """Active ou désactive le flag d'arrêt"""
    global STOP_PREDICTION_FLAG
    STOP_PREDICTION_FLAG = value

def check_stop_flag():
    """Vérifie si l'arrêt a été demandé"""
    return STOP_PREDICTION_FLAG

def get_db_connection():
    """Connexion à la base de données"""
    return mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database,
        charset="utf8"
    )

def create_prediction_table():
    """Crée la table de prédictions si elle n'existe pas"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS `2026_solarx_predictions` (
          `id` INT AUTO_INCREMENT PRIMARY KEY,
          `idpoint` INT NOT NULL,
          `date_prediction` DATE NOT NULL,
          `temperature` FLOAT,
          `ensoleillement` FLOAT,
          `precipitation` FLOAT,
          `irradiance` FLOAT,
          `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          UNIQUE KEY `unique_point_date` (`idpoint`, `date_prediction`),
          FOREIGN KEY (`idpoint`) REFERENCES `2026_solarx_pointsgps`(`idpoint`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)
    
    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Table 2026_solarx_predictions créée/vérifiée")

def check_predictions_exist():
    """Vérifie si des prédictions existent déjà dans la BDD"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM `2026_solarx_predictions`")
    count = cursor.fetchone()[0]
    
    cursor.close()
    conn.close()
    
    return count > 0

def get_all_points():
    """Récupère tous les points GPS disponibles"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT idpoint, adresse 
        FROM 2026_solarx_pointsgps 
        ORDER BY idpoint
    """)
    
    points = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return points

def get_last_historical_date():
    """Récupère la dernière date disponible dans les données historiques"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT MAX(date_collecte) 
        FROM 2026_solarx_mesures
    """)
    
    last_date = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    
    return last_date

def load_historical_data(idpoint):
    """Charge les données historiques pour un point GPS"""
    conn = get_db_connection()
    
    query = """
        SELECT 
            date_collecte as ds,
            temperature,
            ensoleillement,
            precipitation,
            irradiance
        FROM 2026_solarx_mesures
        WHERE idpoint = %s
        AND date_collecte >= '2019-01-01'
        ORDER BY date_collecte
    """
    
    df = pd.read_sql(query, conn, params=(idpoint,))
    conn.close()
    
    # Convertir la colonne ds en datetime
    df['ds'] = pd.to_datetime(df['ds'])
    
    return df

def train_prophet_model(df, variable_name):
    """
    Entraîne un modèle Prophet pour une variable avec saisonnalité
    df : DataFrame avec colonnes 'ds' (date) et la variable
    variable_name : 'temperature', 'ensoleillement', 'precipitation', 'irradiance'
    """
    # Préparer les données pour Prophet
    df_prophet = df[['ds', variable_name]].copy()
    df_prophet.columns = ['ds', 'y']
    df_prophet = df_prophet.dropna()
    
    if len(df_prophet) < 100:
        return None
    
    # Configuration Prophet avec forte saisonnalité
    model = Prophet(
        yearly_seasonality=True,        # Capture été/hiver
        weekly_seasonality=True,         # Capture variations hebdo
        daily_seasonality=False,
        changepoint_prior_scale=0.05,   # Flexibilité tendance
        seasonality_prior_scale=15.0,   # Force de saisonnalité élevée
        seasonality_mode='multiplicative' if variable_name in ['ensoleillement', 'precipitation'] else 'additive',
        interval_width=0.95,            # Intervalle de confiance
    )
    
    # Ajouter saisonnalité mensuelle personnalisée
    model.add_seasonality(
        name='monthly',
        period=30.5,
        fourier_order=5
    )
    
    # Entraîner le modèle
    model.fit(df_prophet)
    
    return model

def predict_period(model, start_date, days):
    """
    Génère les prédictions pour une période donnée
    start_date : date de début (datetime)
    days : nombre de jours à prédire
    """
    # Créer les dates futures
    future_dates = pd.date_range(start=start_date, periods=days, freq='D')
    future = pd.DataFrame({'ds': future_dates})
    
    # Faire les prédictions
    forecast = model.predict(future)
    
    return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]

def get_days_from_period(period):
    """Convertit la période sélectionnée en nombre de jours"""
    periods = {
        '1_day': 1,
        '1_week': 7,
        '1_month': 30,
        '6_months': 180,
        '1_year': 365,
        '5_years': 1825
    }
    return periods.get(period, 365)

def predict_for_point(idpoint, period='1_year', callback=None):
    """
    Génère les prédictions pour un point GPS spécifique
    callback : fonction appelée pour mettre à jour le statut
    """
    # Vérifier si l'arrêt a été demandé
    if check_stop_flag():
        if callback:
            callback(idpoint, "stopped", "Arrêté par l'utilisateur")
        return False
    
    try:
        # Charger données historiques
        df_hist = load_historical_data(idpoint)
        
        if df_hist.empty or len(df_hist) < 100:
            if callback:
                callback(idpoint, "error", "Pas assez de données historiques")
            return False
        
        # Calculer la date de début (lendemain de la dernière date historique)
        last_date = df_hist['ds'].max()
        start_date = last_date + timedelta(days=1)
        
        # Nombre de jours à prédire
        days = get_days_from_period(period)
        
        # Prédire chaque variable
        predictions = {}
        variables = ['temperature', 'ensoleillement', 'precipitation', 'irradiance']
        
        for i, var in enumerate(variables):
            # Vérifier à nouveau si arrêt demandé
            if check_stop_flag():
                if callback:
                    callback(idpoint, "stopped", "Arrêté par l'utilisateur")
                return False
            
            if callback:
                callback(idpoint, "progress", f"Prédiction {var}... ({i+1}/{len(variables)})")
            
            if var in df_hist.columns and df_hist[var].notna().sum() > 100:
                try:
                    model = train_prophet_model(df_hist, var)
                    if model:
                        forecast = predict_period(model, start_date, days)
                        predictions[var] = forecast['yhat'].values
                        predictions[f'{var}_lower'] = forecast['yhat_lower'].values
                        predictions[f'{var}_upper'] = forecast['yhat_upper'].values
                        predictions['dates'] = forecast['ds']
                except Exception as e:
                    print(f"❌ Erreur pour {var}: {e}")
                    predictions[var] = [None] * days
        
        # Insérer dans la BDD
        if predictions and 'dates' in predictions:
            insert_predictions(idpoint, predictions)
            if callback:
                callback(idpoint, "success", "Prédictions terminées")
            return True
        
    except Exception as e:
        if callback:
            callback(idpoint, "error", str(e))
        print(f"❌ Erreur globale pour idpoint {idpoint}: {e}")
        return False

def predict_for_all_points(period='1_year', callback=None):
    """
    Génère les prédictions pour tous les points GPS
    callback : fonction pour mettre à jour l'interface
    """
    # Réinitialiser le flag d'arrêt au début
    set_stop_flag(False)
    
    points = get_all_points()
    
    if callback:
        callback(None, "start", f"Début des prédictions pour {len(points)} points")
    
    success_count = 0
    for i, point in enumerate(points):
        # Vérifier si l'arrêt a été demandé
        if check_stop_flag():
            if callback:
                callback(None, "stopped", f"Arrêté : {success_count}/{len(points)} points terminés")
            return success_count
        
        idpoint = point['idpoint']
        
        if callback:
            callback(idpoint, "processing", f"Point {i+1}/{len(points)}")
        
        if predict_for_point(idpoint, period, callback):
            success_count += 1
    
    if callback:
        callback(None, "complete", f"Terminé : {success_count}/{len(points)} points")
    
    return success_count

def insert_predictions(idpoint, predictions):
    """Insère les prédictions dans la BDD"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
        INSERT INTO 2026_solarx_predictions 
        (idpoint, date_prediction, temperature, ensoleillement, precipitation, irradiance)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        temperature = VALUES(temperature),
        ensoleillement = VALUES(ensoleillement),
        precipitation = VALUES(precipitation),
        irradiance = VALUES(irradiance)
    """
    
    dates = predictions['dates']
    data = []
    
    for i in range(len(dates)):
        data.append((
            idpoint,
            dates.iloc[i].strftime('%Y-%m-%d'),
            predictions.get('temperature', [None]*len(dates))[i],
            predictions.get('ensoleillement', [None]*len(dates))[i],
            predictions.get('precipitation', [None]*len(dates))[i],
            predictions.get('irradiance', [None]*len(dates))[i]
        ))
    
    cursor.executemany(query, data)
    conn.commit()
    cursor.close()
    conn.close()

def get_comparison_data(idpoint, variable='temperature'):
    """Récupère données historiques + prédictions pour comparaison"""
    conn = get_db_connection()
    
    # Données historiques
    query_hist = f"""
        SELECT date_collecte as date, {variable} as value, 'Historique' as type
        FROM 2026_solarx_mesures
        WHERE idpoint = %s
        AND date_collecte >= '2019-01-01'
        ORDER BY date_collecte
    """
    
    # Données prédites
    query_pred = f"""
        SELECT date_prediction as date, {variable} as value, 'Prédiction' as type
        FROM 2026_solarx_predictions
        WHERE idpoint = %s
        ORDER BY date_prediction
    """
    
    df_hist = pd.read_sql(query_hist, conn, params=(idpoint,))
    df_pred = pd.read_sql(query_pred, conn, params=(idpoint,))
    
    conn.close()
    
    # Combiner
    df_combined = pd.concat([df_hist, df_pred], ignore_index=True)
    df_combined['date'] = pd.to_datetime(df_combined['date'])
    
    return df_combined

def clear_predictions():
    """Efface toutes les prédictions de la BDD"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM `2026_solarx_predictions`")
    
    conn.commit()
    cursor.close()
    conn.close()
    print("🗑️ Toutes les prédictions ont été effacées")

# Initialisation au démarrage
try:
    create_prediction_table()
    print("✅ Module prediction_prophet initialisé")
except Exception as e:
    print(f"⚠️ Erreur initialisation prediction_prophet: {e}")