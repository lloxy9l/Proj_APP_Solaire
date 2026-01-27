# 📊 Configuration Prometheus + Grafana pour SolarX

Ce dossier contient la configuration complète du monitoring avec Prometheus et Grafana.

## 🚀 Démarrage rapide

### Option 1 : Monitoring seul (si vous avez déjà les services principaux)

```bash
cd docker
docker compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d
```

### Option 2 : Tout démarrer ensemble

```bash
cd docker
docker compose -f docker-compose.yml up -d
docker compose -f docker-compose.monitoring.yml up -d
```

## 🌐 Accès aux interfaces

| Service | URL | Identifiants |
|---------|-----|--------------|
| **Grafana** | http://localhost:3001 | admin / solarx2026 |
| **Prometheus** | http://localhost:9090 | - |
| **Métriques Python** | http://localhost:8000/metrics | - |
| **Node Exporter** | http://localhost:9100/metrics | - |
| **MySQL Exporter** | http://localhost:9104/metrics | - |
| **cAdvisor** | http://localhost:8080 | - |

## 📈 Métriques disponibles

### Métriques SolarX (custom)
- `solarx_page_views_total` : Nombre de vues par page
- `solarx_zones_loaded` : Nombre de zones industrielles chargées
- `solarx_errors_total` : Nombre d'erreurs par type
- `solarx_db_queries_total` : Nombre de requêtes SQL

### Métriques système
- CPU, RAM, Disk (via Node Exporter)
- Métriques Docker (via cAdvisor)
- Métriques MySQL (via MySQL Exporter)

## 📊 Dashboards Grafana recommandés

1. Connectez-vous à Grafana
2. Allez dans **Dashboards** → **Import**
3. Importez ces dashboards :
   - **1860** : Node Exporter Full
   - **7362** : MySQL Overview
   - **193** : Docker Monitoring

## 🔧 Configuration

### Modifier la rétention des données

Dans `prometheus.yml`, ligne `--storage.tsdb.retention.time=30d` :
- Changez `30d` pour garder les données plus ou moins longtemps
- Exemples : `7d`, `90d`, `1y`

### Changer le mot de passe Grafana

Dans `docker-compose.monitoring.yml` :
```yaml
environment:
  - GF_SECURITY_ADMIN_PASSWORD=votre_nouveau_mot_de_passe
```

## 🛠️ Commandes utiles

### Vérifier les métriques Python
```bash
curl http://localhost:8000/metrics
```

### Voir les logs Prometheus
```bash
docker logs prometheus
```

### Voir les logs Grafana
```bash
docker logs grafana
```

### Arrêter le monitoring
```bash
docker compose -f docker-compose.monitoring.yml down
```

### Supprimer les données (reset)
```bash
docker compose -f docker-compose.monitoring.yml down -v
```

## 📝 Ajouter vos propres métriques

Dans votre code Python :

```python
from metrics import track_page_view, track_error, update_zones_count

# Tracker une vue de page
track_page_view('ma-nouvelle-page')

# Tracker une erreur
track_error('database')

# Mettre à jour une gauge
update_zones_count(42)
```

## ⚠️ Troubleshooting

### Prometheus ne démarre pas
- Vérifiez que le port 9090 est libre : `lsof -i :9090`
- Vérifiez les logs : `docker logs prometheus`

### Grafana ne se connecte pas à Prometheus
- Vérifiez que les conteneurs sont sur le même réseau
- Testez : `docker exec grafana ping prometheus`

### Métriques Python non disponibles
- Vérifiez que `prometheus-client` est installé
- Vérifiez l'endpoint : `curl http://localhost:8000/metrics`
- Vérifiez que le port 8000 est exposé dans docker-compose.yml

## 📦 Architecture

```
┌─────────────────┐
│  Application    │ ──► Expose /metrics
│  Python (8050)  │
└─────────────────┘
         │
         │ Scrape toutes les 15s
         ▼
┌─────────────────┐
│   Prometheus    │ ──► Stockage TSDB
│     (9090)      │
└─────────────────┘
         │
         │ Requêtes PromQL
         ▼
┌─────────────────┐
│    Grafana      │ ──► Visualisation
│     (3001)      │
└─────────────────┘
```

## 🎯 Prochaines étapes

1. ✅ Configurez des alertes dans Prometheus
2. ✅ Créez des dashboards personnalisés dans Grafana
3. ✅ Ajoutez plus de métriques métier (temps de requête, etc.)
4. ✅ Configurez des notifications (email, Slack, etc.)
