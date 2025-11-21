FROM python:3.10-slim

# Variables d'environnement
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Installation des dépendances système pour osmnx/geopandas
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    libspatialindex-dev \
    libgeos-dev \
    libproj-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Met à jour pip
RUN pip install --upgrade pip

# Installation des dépendances Python
RUN pip install --no-cache-dir \
    dash==2.14.0 \
    dash-bootstrap-components==1.5.0 \
    plotly==5.18.0 \
    mysql-connector-python==8.2.0 \
    pandas==2.1.3 \
    numpy \
    geopandas==0.14.1 \
    osmnx==1.8.1 \
    scikit-learn==1.3.2 \
    shapely==2.0.2 \
    pyproj==3.6.1 \
    rtree==1.1.0

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers de l'application
COPY . /app

# Lancement de l'application
CMD ["python", "dashboard.py"]