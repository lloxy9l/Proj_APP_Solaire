const express = require('express');
const mysql = require('mysql2');
const cors = require('cors');
const retry = require('retry');  // Utilisation de la bibliothèque retry

const app = express();
const port = 3000;

app.use(cors()); // Permet à votre frontend de communiquer avec ce serveur

// Fonction pour se connecter à la base de données avec réessai
let pool;  // Pool de connexions MySQL (plus robuste qu'une seule connexion)

function initPool() {
  const operation = retry.operation({ retries: 5, factor: 2, minTimeout: 2000 });

  // Fermer l'ancien pool si présent pour éviter de conserver des sockets mortes
  if (pool) {
    pool.end(() => {});
  }

  operation.attempt((currentAttempt) => {
    // Créer un pool de connexions pour éviter les coupures de socket et gérer les reconnections
    pool = mysql.createPool({
      host: process.env.DB_HOST || 'db',  // Permet de surcharger l'hôte via l'environnement
      user: 'root',
      password: 'rootpassword',
      database: 'projet_solarx',
      waitForConnections: true,
      connectionLimit: 10,
      queueLimit: 0,
      enableKeepAlive: true,
      keepAliveInitialDelay: 10000,
      connectTimeout: 20000,
    });

    // Vérifie la connexion initiale
    pool.getConnection((err, connection) => {
      if (err && operation.retry(err)) {
        console.log(`Tentative de connexion ${currentAttempt} échouée, réessayer...`);
        return;
      } else if (err) {
        console.error('Échec de la connexion après plusieurs tentatives :', err);
        return;
      }

      console.log('Connecté à la base de données');

      // Surveiller les erreurs fatales des connexions du pool
      connection.on('error', (poolErr) => {
        console.error('Erreur de connexion MySQL détectée :', poolErr);
        if (poolErr && poolErr.fatal) {
          console.log('Recréation du pool MySQL...');
          initPool();
        }
      });

      connection.release();
    });
  });
}

// Connexion à la base de données au démarrage
initPool();

// Endpoint pour récupérer les points avec les données météo
app.get('/getPoints', (req, res) => {
  if (!pool) {
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

  pool.query(query, (err, results) => {
    if (err) {
      console.error('Erreur lors de la récupération des données:', err);
      if (err.fatal) {
        console.log('Erreur fatale détectée, recréation du pool...');
        initPool();
      }
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
