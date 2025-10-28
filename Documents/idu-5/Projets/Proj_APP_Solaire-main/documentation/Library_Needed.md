# Installation des dépendances

Avant d'exécuter le programme, assurez-vous d'avoir installé les bibliothèques et modules nécessaires. Vous pouvez les installer en exécutant la commande suivante :

```bash
pip install -r requirements.txt
```

Assurez-vous également d'avoir une connexion Internet active pour l'installation des bibliothèques via pip.

## Liste des dépendances

- **mysql-connector-python**: Bibliothèque Python permettant de se connecter à des bases de données MySQL.
  
- **geopy**: Bibliothèque Python pour géocoder des adresses, calculer des distances géodésiques et plus encore.

- **openmeteo-requests**: Bibliothèque Python pour récupérer des données météorologiques à partir d'OpenMeteo.

- **requests-cache**: Bibliothèque Python pour le cache des requêtes HTTP, permettant de réduire le temps de chargement en mémorisant les réponses précédentes.

- **pandas**: Bibliothèque Python pour la manipulation et l'analyse des données.

- **retry-requests**: Bibliothèque Python pour la gestion des tentatives de requête HTTP répétées en cas d'échec.

- **beautifulsoup4**: Bibliothèque Python pour l'analyse HTML et XML. Elle fournit des moyens pour extraire des données de fichiers HTML et XML.

- **selenium**: Bibliothèque Python pour automatiser les actions dans un navigateur Web. Utile pour les tâches telles que le scraping web et les tests automatisés.

## Installation du chromedriver.exe

Pour utiliser Selenium avec Google Chrome, vous devez télécharger le chromedriver.exe correspondant à votre version de Google Chrome. Vous pouvez télécharger le chromedriver.exe à partir du lien suivant :

[Chromedriver.exe - Téléchargement](https://storage.googleapis.com/chrome-for-testing-public/122.0.6261.128/win64/chromedriver-win64.zip)

Une fois téléchargé, extrayez le fichier chromedriver.exe et assurez-vous de l'ajouter dans votre PATH système ou de spécifier son emplacement dans votre script Selenium.

## Installation manuelle

Si vous préférez, vous pouvez installer les dépendances Python manuellement en utilisant les commandes suivantes :

```bash
pip install mysql-connector-python
pip install geopy
pip install openmeteo-requests
pip install requests-cache
pip install pandas
pip install retry-requests
pip install beautifulsoup4
pip install selenium
```

Assurez-vous de remplacer `pip` par `pip3` si vous utilisez Python 3.

---
**Note :** Il est recommandé d'utiliser un environnement virtuel Python pour éviter les conflits de dépendances.
