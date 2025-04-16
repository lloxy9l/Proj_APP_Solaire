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
      host: 'db',  // Utiliser le nom du service Docker 'db'
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

// Créer une route pour récupérer les points GPS
app.get('/getPoints', (req, res) => {
  if (!db) {
    return res.status(500).json({ error: 'La connexion à la base de données n\'est pas encore établie.' });
  }

  const query = `
    SELECT 
      p.latitude, 
      p.longitude,
      d.temperature,
      d.ensoleillement,
      d.irradiance,
      d.precipitation,
      d.date_collecte
    FROM 2026_solarx_pointsgps p
    JOIN 2026_solarx_donnees d ON p.id = d.idpoint
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
