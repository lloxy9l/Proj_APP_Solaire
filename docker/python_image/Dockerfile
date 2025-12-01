FROM python:3.10-slim

WORKDIR /usr/src/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Met à jour pip et installe les dépendances (sans cache) pour alléger l'image
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir dash dash-bootstrap-components plotly mysql-connector-python pandas google-genai

# Lancement de l'application (le code est monté via docker-compose)
CMD ["python", "dashboard.py"]
