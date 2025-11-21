# Utiliser l'image officielle MySQL comme base
FROM mysql:latest

# Copier le fichier SQL pour initialiser la base de données
COPY ./projet_solarx.sql /docker-entrypoint-initdb.d/

# Optionnel : Tu peux définir des variables d'environnement pour la base de données
ENV MYSQL_ROOT_PASSWORD=rootpassword
ENV MYSQL_DATABASE=projet_solarx
ENV MYSQL_USER=dev
ENV MYSQL_PASSWORD=password
