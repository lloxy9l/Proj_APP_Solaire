
<?php
    include('config_bdd.php');

    $conn = new mysqli($servername, $username, $password, $database);

    if ($conn->connect_error) {
        $msg = "erreur ". $conn->connect_error;
    }

    $host_info = mysqli_get_host_info($conn);

    $server_info = mysqli_get_server_info($conn);


    mysqli_query($conn, "SET NAMES UTF8");
?>

<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SolarX - Page de présentation</title>
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-title" content="SolarX - Page de présentation">
    <meta name="application-name" content="SolarX - Page de présentation">
    <link rel="icon" href="assets/img/icon.ico" type="image/x-icon">
    <link rel="stylesheet" href="assets/css/style.css">
    <link rel="stylesheet" href="assets/css/responsive.css">
</head>
<body>

    <div class="background_div" id="home">
        <header class="header bg_grid">
            <div class="logo">
                <img src="assets/img/logo_home_page.png" alt="logo">
            </div>
            <div class="menu_bar">
                <!-- Le bouton du menu déroulant -->
                <button class="menu_btn">Menu</button>
                <!-- Le contenu du menu déroulant -->
                <div class="links_home_page">
                    <a href="#home">Accueil</a>
                    <a href="#projet">Notre projet</a>
                    <a href="#team">L'équipe</a>
                </div>
            </div>
            <div class="link_dashboard_header">
            <?php
                    //récuperer les dates max et min
                    $sql = "SELECT get_date_max('Genève, Schweiz/Suisse/Svizzera/Svizra') AS max_date;";
                    $result = $conn->query($sql);

                    if ($result->num_rows > 0) {
                        $row = $result->fetch_assoc();
                        $datemax = $row['max_date'];
                    }
                    $sql = "SELECT get_date_min('Genève, Schweiz/Suisse/Svizzera/Svizra') AS min_date;";
                    $result = $conn->query($sql);

                    if ($result->num_rows > 0) {
                        $row = $result->fetch_assoc();
                        $datemin = $row['min_date'];
                    }
                    echo"<a href='../Dashboard_web_new_design/dashboard.php?parametre1=precipitation&parametre2=ensoleillement&date_debut=$datemin&date_fin=$datemax' class='link_dashboard'>Voir les données</a>";

                    ?>
            </div>
        </header>

        <div class="home_presentation">
            <p class="title">Un nouveau moyen de visualiser vos données.</p>
            <p class="subtitle">Arrêtez de gaspiller du temps et de l'argent afin de pouvoir visualiser des données sur notre avenir énergétique.</p>
            <?php
                //récuperer les dates max et min
                $sql = "SELECT get_date_max('Genève, Schweiz/Suisse/Svizzera/Svizra') AS max_date;";
                $result = $conn->query($sql);

                if ($result->num_rows > 0) {
                    $row = $result->fetch_assoc();
                    $datemax = $row['max_date'];
                }
                $sql = "SELECT get_date_min('Genève, Schweiz/Suisse/Svizzera/Svizra') AS min_date;";
                $result = $conn->query($sql);

                if ($result->num_rows > 0) {
                    $row = $result->fetch_assoc();
                    $datemin = $row['min_date'];
                }
                echo"<a href='../Dashboard_web_new_design/dashboard.php?parametre1=precipitation&parametre2=ensoleillement&date_debut=$datemin&date_fin=$datemax' class='link_dashboard'>Voir les données</a>";
                ?>
        </div>
    </div>

        <div class="container_card_info bg_grid">
            <div class="card">
                <img src="assets/img/icons8-idée-96.png" alt="">
                <p class="title">Un projet ambitieux</p>
                <p class="subtitle">Un projet sur 3 ans au sein de la formation Informatique Données Usages.</p>
            </div>
            <div class="card">
                <img src="assets/img/icons8-base-de-données-96.png" alt="">
                <p class="title">Des données réelles</p>
                <p class="subtitle">Inclut des données de luminosité, irradiance, température et precipitation.</p>
            </div>
            <div class="card">
                <img src="assets/img/icons8-feuille-96.png" alt="">
                <p class="title">Vers une transition énergétique</p>
                <p class="subtitle">Fournir des informations météorologiques complètes et fiables.</p>
            </div>
        </div>

        <div class="container_our_projet bg_grid" id="projet">
            <div class="container_txt_project">
                <p class="title">Notre Projet</p>
                <p class="title2">Un projet à dimension réelle.</p>
                <div class="description">
                    <div class="card">
                        <p><b>Collecte de données météo pour Genève :</b> Le projet vise à collecter diverses données météo pour la région de Genève, comme la luminosité, l'irradiance, la température et les précipitations, pour soutenir la planification urbaine et les projets agricoles et énergétiques.</p>
                    </div>
                    <div class="card">
                        <p><b>Web scraping avancé : </b>Nous utilisons des techniques de web scraping robustes pour obtenir des données précises et à jour à partir de sources fiables.</p>
                    </div>
                    <div class="card">
                        <p><b>Stockage sécurisé : </b>Les données sont stockées dans une base de données relationnelle interne, assurant une gestion efficace, une évolutivité et une sécurité accrue.</p>
                    </div>
                </div>
            </div>
            <div>
                <img class="dashboard_img1" src="assets/img/dashboard.png" alt="">
            </div>
        </div>

        <div class="container_ui bg_grid">
            <div class="container_txt_UX">
                <p class="title" id="UX_title">Une expérience axée sur l'utilisateur</p>
                <p class="subtitle">Une expérience utilisateur fluide et intuitive, permettant un accès facile aux données météorologiques de Genève pour des décisions éclairées en urbanisme, agriculture et énergie renouvelable.</p>
            </div>
            <img src="assets/img/dashboard.png" alt="">
            <div class="flex_infos">
                <div style="width: 300px;">
                    <p class="title">UI / UX</p>
                    <p>Designer pour votre confort et pour offrir une simplicité.</p>
                </div>
                <div style="width: 300px;">
                    <p class="title">Un visuel immersif</p>
                    <p>Obtenez l'information en un coup d'oeil seulement.</p>
                </div>
                <div style="width: 300px;">
                    <p class="title">Mobile - friendly</p>
                    <p>Optimiser aussi pour votre smartphone.</p>
                </div>
            </div>
        </div>
        <div style="margin-top: 200px;" class="bg_grid" id="offres">
            <p class="title2">Nos offres</p>
            <br>
            <div class="container_prices">
                <div class="card_price_silver">
                    <div class="card_price_silver_header">
                        <div class="silver"></div>
                        <p style="font-weight: bold;">Argent</p>
                    </div>
                    <p>* Limité à 50 requêtes / jour</p>
                    <p class="price">70€ <span> /mois</span></p>
                    <ul class="featureList">
                        <li>Accès complet au dashboard.</li>
                        <li>Visualisation des données.</li>
                        <li class="disabled">Nombre de requêtes ilimitées. *</li>
                        <li class="disabled">Intégration d'autres villes.</li>
                    </ul>
                </div>
                <div class="card_price_gold">
                    <div class="card_price_gold_header">
                        <div class="gold"></div>
                        <p style="font-weight: bold;">Or</p>
                    </div>
                    <p>* Limité à 100 requêtes / jour</p>
                    <p class="price">90€ <span> /mois</span></p>
                    <ul class="featureList">
                        <li>Accès complet au dashboard.</li>
                        <li>Visualisation des données.</li>
                        <li>Intégration d'autres villes.</li>
                        <li class="disabled">Nombre de requêtes ilimitées.*</li>
                    </ul>
                </div>
                <div class="card_price_paltinum">
                    <div class="card_price_paltinum_header">
                        <div class="paltinum"></div>
                        <p style="color: #fff; font-weight: bold;">paltinum</p>
                    </div>
                    <p>Requêtes illimitées</p>
                    <p style="color: #fff;" class="price">130€ <span style="color: #fff;"> /mois</span></p>
                    <ul class="featureList_paltinum">
                        <li>Accès complet au dashboard.</li>
                        <li>Visualisation des données.</li>
                        <li>Intégration d'autres villes.</li>
                        <li>Nombre de requêtes ilimitées.</li>
                    </ul>
                </div>
            </div>
        </div>

        <div class="container_team bg_grid" id="team">
            <p class="title2" id="TEAM_title">Notre équipe</p>
            <p class="subtitle"></p>
            <img src="assets/img/team.png" alt="">
        </div>

    <div class="container_eco">
        <p>Vers une transition écologique grâce aux données.</p>
    </div>

    <footer>
        <div class="block_footer">
            <div class="about_footer">
                <p class="footer_title">A propos</p>
                <p>Merci de visiter notre site de prévisualisation pour notre service de tableau de bord météo dédié à Genève. Notre objectif est de fournir un aperçu de nos fonctionnalités avancées et de la précision de nos données météorologiques pour répondre à vos besoins en urbanisme, agriculture et énergie renouvelable dans la région de Genève.</p>
            </div>
                <div class="categories_footer">
                    <p class="footer_title">Catégories</p>
                    <a href="#home">Accueil</a>
                    <a href="#projet">Notre projet</a>
                    <a href="#team">L'équipe</a>
                    <a href="#offres">Offres</a>
                </div>
                <div class="terms_footer">
                    <p class="footer_title">Juridiction</p>
                    <a href="terms/mentions.html">Mentions Légales</a>
                </div>
        </div>
        <hr>
        <p class="copyright">Copyright &copy; 2024 Tous Droits Réservés</p>

    </footer>

</body>
</html>
