"""
Module de métriques Prometheus pour SolarX Dashboard
Expose les métriques de performance et d'utilisation de l'application
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY
from flask import Response
import time
import functools

# ============================================
# DÉFINITION DES MÉTRIQUES
# ============================================

# Compteurs - valeurs qui ne font qu'augmenter
page_views = Counter(
    'solarx_page_views_total', 
    'Nombre total de vues de pages',
    ['page']
)

errors = Counter(
    'solarx_errors_total', 
    'Nombre total d\'erreurs',
    ['type']
)

db_queries = Counter(
    'solarx_db_queries_total',
    'Nombre total de requêtes à la base de données',
    ['query_type']
)

# Histogrammes - distribution de valeurs (latence)
request_duration = Histogram(
    'solarx_request_duration_seconds',
    'Durée des requêtes en secondes',
    ['endpoint']
)

db_query_duration = Histogram(
    'solarx_db_query_duration_seconds',
    'Durée des requêtes SQL en secondes',
    ['query_type']
)

# Gauges - valeurs qui peuvent monter ou descendre
active_users = Gauge(
    'solarx_active_users',
    'Nombre d\'utilisateurs actuellement actifs'
)

db_connections = Gauge(
    'solarx_db_connections',
    'Nombre de connexions actives à la base de données'
)

cache_size = Gauge(
    'solarx_cache_size_bytes',
    'Taille du cache en bytes'
)

zones_loaded = Gauge(
    'solarx_zones_loaded',
    'Nombre de zones industrielles chargées'
)

# ============================================
# FONCTIONS D'AIDE
# ============================================

def metrics_endpoint():
    """
    Endpoint Flask pour exposer les métriques au format Prometheus
    Utilisation: @app.route('/metrics')
    """
    return Response(generate_latest(REGISTRY), mimetype='text/plain')


def track_page_view(page_name):
    """
    Incrémenter le compteur de vues pour une page donnée
    
    Args:
        page_name (str): Nom de la page (ex: 'home', 'ensoleillement', 'temperature')
    """
    page_views.labels(page=page_name).inc()


def track_error(error_type):
    """
    Incrémenter le compteur d'erreurs
    
    Args:
        error_type (str): Type d'erreur (ex: 'database', 'api', 'validation')
    """
    errors.labels(type=error_type).inc()


def track_db_query(query_type):
    """
    Incrémenter le compteur de requêtes DB
    
    Args:
        query_type (str): Type de requête (ex: 'select', 'insert', 'update')
    """
    db_queries.labels(query_type=query_type).inc()


def time_function(metric_histogram, label=None):
    """
    Décorateur pour mesurer le temps d'exécution d'une fonction
    
    Args:
        metric_histogram: Histogramme Prometheus à utiliser
        label: Label à appliquer (optionnel)
    
    Exemple:
        @time_function(request_duration, 'get_weather_data')
        def get_weather_data():
            pass
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                if label:
                    metric_histogram.labels(endpoint=label).observe(duration)
                else:
                    metric_histogram.labels(endpoint=func.__name__).observe(duration)
        return wrapper
    return decorator


def update_zones_count(count):
    """
    Mettre à jour le nombre de zones industrielles chargées
    
    Args:
        count (int): Nombre de zones
    """
    zones_loaded.set(count)


def update_cache_size(size_bytes):
    """
    Mettre à jour la taille du cache
    
    Args:
        size_bytes (int): Taille en bytes
    """
    cache_size.set(size_bytes)


# ============================================
# EXEMPLE D'UTILISATION
# ============================================
"""
# Dans dashboard.py:

from metrics import metrics_endpoint, track_page_view, track_error, time_function, request_duration

# Exposer l'endpoint /metrics
@server.route('/metrics')
def metrics():
    return metrics_endpoint()

# Tracker les vues de pages
@app.callback(...)
def update_page_content(pathname):
    track_page_view(pathname.strip('/') or 'home')
    # ... reste du code

# Mesurer le temps d'exécution
@time_function(request_duration, 'load_weather_data')
def load_weather_data():
    # ... votre code
    pass
"""
