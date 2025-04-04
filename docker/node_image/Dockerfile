# Étape 1: Utiliser une image officielle de Node.js
FROM node:latest

# Étape 2: Créer et définir le répertoire de travail dans le conteneur
WORKDIR /app

# Étape 3: Copier package.json et installer les dépendances
COPY package.json /app/
RUN npm install

# Étape 4: Copier le reste de l'application
COPY . /app/

# Étape 5: Exposer le port sur lequel le serveur va écouter
EXPOSE 3000

# Étape 6: Lancer l'application
CMD ["npm", "start"]
