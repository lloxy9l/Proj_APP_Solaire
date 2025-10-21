const express = require('express');
const mysql = require('mysql2');
const cors = require('cors');
const retry = require('retry');  // Utilisation de la bibliothèque retry

const app = express();
const port = 3000;

app.use(cors()); // Permet à votre frontend de communiquer avec ce serveur

// Fonction pour se connecter à la base de données avec réessai
let db;  // Déclarer db en dehors de la fonction

function connectToDatabase() {
  const operation = retry.operation({ retries: 5, factor: 2, minTimeout: 2000 });

  operation.attempt((currentAttempt) => {
    // Créer une nouvelle connexion à la base de données
    db = mysql.createConnection({
      host: process.env.DB_HOST || 'db',  // Permet de surcharger l'hôte via l'environnement
      user: 'root',
      password: 'rootpassword',
      database: 'projet_solarx',
    });

    // Tentative de connexion
    db.connect((err) => {
      if (err) {
        if (operation.retry(err)) {
          console.log(`Tentative de connexion ${currentAttempt} échouée, réessayer...`);
          return;
        }
        console.error('Échec de la connexion après plusieurs tentatives :', err);
        return;
      }
      console.log('Connecté à la base de données');
    });
  });
}

// Connexion à la base de données au démarrage
connectToDatabase();

// Endpoint pour récupérer les points avec les données météo
app.get('/getPoints', (req, res) => {
  if (!db) {
    return res.status(500).json({ error: 'La connexion à la base de données n\'est pas encore établie.' });
  }

  const query = `
  SELECT 
    p.latitude, 
    p.longitude,
    ROUND(AVG(m.temperature), 2) AS temperature,
    ROUND(AVG(m.ensoleillement), 2) AS ensoleillement,
    ROUND(AVG(m.irradiance), 2) AS irradiance,
    ROUND(AVG(m.precipitation), 2) AS precipitation
  FROM 2026_solarx_pointsgps p
  JOIN 2026_solarx_mesures m ON p.idpoint = m.idpoint
  GROUP BY p.latitude, p.longitude
  `;

  db.query(query, (err, results) => {
    if (err) {
      console.error('Erreur lors de la récupération des données:', err);
      res.status(500).json({ error: 'Erreur lors de la récupération des données' });
      return;
    }
    res.json(results);
  });
});

// 🔊 Démarrer le serveur
app.listen(port, () => {
  console.log(`🟢 Serveur démarré sur http://localhost:${port}`);
});
