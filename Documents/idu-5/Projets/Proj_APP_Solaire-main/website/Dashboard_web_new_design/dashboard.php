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
    <title>SolarX - Tableau de bord</title>
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-title" content="SolarX - Page de présentation">
    <meta name="application-name" content="SolarX - Page de présentation">
    <!-- <link rel="apple-touch-icon" href="assets/img/icon_mobile.ico"> -->
    <link rel="stylesheet" href="assets/css/dashboard.css">
    <link rel="stylesheet" href="assets/css/responsive.css">

</head>

<body>

<header>
        <div class="logo">
            <a href="../Home_Page_Solar/index.php"><img src="assets/img/logo_dashboard.png" alt=""></a>
        </div>
        <div id="searchbar">
            <div id="searchbarcontainer">
                <ion-icon name="search" class="search_icon"></ion-icon>

                <input type="text" id="nom_zone" placeholder="Rechercher une ville" value="">
            </div>
            <div id="resultcontainer"></div>
        </div>
        <a id="change_settings" href="#"><ion-icon name="layers"></ion-icon></a>
        <div class="icon_search_responsive">
            <ion-icon name="search" class="search_icon"></ion-icon>
        </div>
    </header>

    <div class="nav_bar_responsive">
    </div>

    <aside>
        <form action="dashboard.php" method="get">
        <?php
            $parametre1 = isset($_GET["parametre1"]) ? $_GET["parametre1"] : "";
            $parametre2 = isset($_GET["parametre2"]) ? $_GET["parametre2"] : "";

        ?>
        <div id=bar_lateral>

                <div class="radio-container">
                    <p>Type graph 1</p>

                    <div class="radio-container_item">
                        <div>
                            <img src="assets/img/icons8-pluie-96.png" alt="">
                            <label for="precipitation">Précipitation</label>
                        </div>
                        <input type="radio" id="precipitation" name="parametre1" value="precipitation" <?php if($parametre1 === "precipitation") echo "checked"; ?>>
                    </div>

                    <div class="radio-container_item">
                        <div>
                            <img src="assets/img/icons8-lightning-bolt-100.png" alt="">
                            <label for="irradiance">Irradiance</label>
                        </div>
                            <input type="radio" id="irradiance" name="parametre1" value="irradiance"<?php if($parametre1 === "irradiance") echo "checked"; ?>>
                    </div>

                    <div class="radio-container_item">
                        <div>
                            <img src="assets/img/icons8-soleil-96.png" alt="">
                            <label for="ensoleillement">Ensoleillement</label>
                        </div>
                        <input type="radio" id="ensoleillement" name="parametre1" value="ensoleillement"<?php if($parametre1 === "ensoleillement") echo "checked"; ?>>
                    </div>

                    <div class="radio-container_item">
                        <div>
                            <img src="assets/img/icons8-thermomètre-96.png" alt="">
                            <label for="temperature">Température</label>
                        </div>
                        <input type="radio" id="temperature" name="parametre1" value="temperature"<?php if($parametre1 === "temperature") echo "checked"; ?>>
                    </div>


                </div>

                <div class="radio-container">
                    <p>Type graph 2</p>
                    <div class="radio-container_item">
                    <div>
                        <img src="assets/img/icons8-pluie-96.png" alt="">
                        <label for="precipitation2">Précipitation</label>
                    </div>
                    <input type="radio" id="precipitation2" name="parametre2" value="precipitation"<?php if($parametre2 === "precipitation") echo "checked"; ?>>
                    </div>

                    <div class="radio-container_item">
                        <div>
                            <img src="assets/img/icons8-lightning-bolt-100.png" alt="">
                            <label for="irradiance2">Irradiance</label>
                        </div>
                        <input type="radio" id="irradiance2" name="parametre2" value="irradiance"<?php if($parametre2 === "irradiance") echo "checked"; ?>>
                    </div>

                    <div class="radio-container_item">
                        <div>
                            <img src="assets/img/icons8-soleil-96.png" alt="">
                            <label for="ensoleillement2">Ensoleillement</label>
                        </div>
                        <input type="radio" id="ensoleillement2" name="parametre2" value="ensoleillement"<?php if($parametre2 === "ensoleillement") echo "checked"; ?>>
                    </div>

                    <div class="radio-container_item">
                        <div>
                            <img src="assets/img/icons8-thermomètre-96.png" alt="">
                            <label for="temperature2">Température</label>
                        </div>
                        <input type="radio" id="temperature2" name="parametre2" value="temperature"<?php if($parametre2 === "temperature") echo "checked"; ?>>
                    </div>
                </div>
                <div id="date_container">
                    <p>Sélection de la période </p>
                    <div class= date>

                        <label for="date_debut">Date de début :</label>
                        <input type="date" id="date_debut" name="date_debut" min="<?php echo date('2024-01-01'); ?>" max="<?php echo date('Y-m-d'); ?>"value="<?php echo $_GET["date_debut"]?>">
                    </div>

                    <div class= date>
                        <label for="date_fin">Date de fin :  </label>
                        <input type="date" id="date_fin" name="date_fin" min="<?php echo date('2024-01-01'); ?>" max="<?php echo date('Y-m-d'); ?>"value="<?php echo $_GET["date_fin"]?>">
                    </div>
                    <input type="submit" value="Envoyer" class="submit-button" style="margin-top: 15px;">
                </div>
            <br>


          </div>
          </form>
    </aside>


    <main>
        <div id="stats">
            <div class="card_stats">
                <div class="key_number">

                <img src="assets/img/icons8-pluie-96.png" alt="">

                    <?php
                    if( isset($_GET["date_debut"]) && isset($_GET["date_fin"])) {
                        $date_debut=$_GET["date_debut"];
                        $date_fin=$_GET["date_fin"];
                        $nom_zone="Genève, Schweiz/Suisse/Svizzera/Svizra";
                        $sql = "SELECT get_mean_precipitation('$date_debut', '$date_fin','$nom_zone') as mean;";
                        $result = $conn->query($sql);

                        if ($result->num_rows > 0) {
                            // Récupérer la ligne de résultat
                            $row = $result->fetch_assoc();
                            // Récupérer la valeur de la colonne mean_temp (ou le nom de votre colonne)
                            $mean_temp = round($row['mean'],3);
                            // Afficher le résultat dans votre page HTML
                            echo "<p>$mean_temp</p>";
                        } else {
                            echo "Aucun résultat trouvé.";
                        }
                    }
                        ?>

                </div>
                <div class="details_key_number">millimètres de précipitation</div>
            </div>
            <div class="card_stats">
                <div class="key_number">
                <img src="assets/img/icons8-soleil-96.png" alt="">

                <?php
                    if( isset($_GET["date_debut"])&& isset($_GET["date_fin"])) {
                        $date_debut=$_GET["date_debut"];
                        $date_fin=$_GET["date_fin"];
                        $nom_zone="Genève, Schweiz/Suisse/Svizzera/Svizra";
                        $sql = "SELECT get_mean_ensoleillement('$date_debut', '$date_fin','$nom_zone') as mean;";
                        $result = $conn->query($sql);

                        if ($result->num_rows > 0) {
                            // Récupérer la ligne de résultat
                            $row = $result->fetch_assoc();
                            // Récupérer la valeur de la colonne mean_temp (ou le nom de votre colonne)
                            $mean_temp = round($row['mean']/3600,2);
                            // Afficher le résultat dans votre page HTML
                            echo "<p>$mean_temp</p>";
                        } else {
                            echo "Aucun résultat trouvé.";
                        }
                    }
                ?>
                </div>
                <div class="details_key_number">heures d'ensoleillement</div>
            </div>
            <div class="card_stats">
                <div class="key_number">
                <img src="assets/img/icons8-lightning-bolt-100.png" alt="">
                    <?php
                    if( isset($_GET["date_debut"])&& isset($_GET["date_fin"])) {
                         $date_debut=$_GET["date_debut"];
                         $date_fin=$_GET["date_fin"];
                         $nom_zone="Genève, Schweiz/Suisse/Svizzera/Svizra";
                         $sql = "SELECT get_mean_irradiance('$date_debut', '$date_fin','$nom_zone') as mean;";
                         $result = $conn->query($sql);

                         if ($result->num_rows > 0) {
                             // Récupérer la ligne de résultat
                             $row = $result->fetch_assoc();
                             // Récupérer la valeur de la colonne mean_ensoleillement
                             $mean_temp = round($row['mean'],3);
                             // Afficher le résultat dans votre page HTML
                             echo "<p>$mean_temp</p>";
                         } else {
                             echo "Aucun résultat trouvé.";
                         }
                     }
                     ?>

                </div>
                <div class="details_key_number">kWh/m² d'irradiation</div>
            </div>
            <div class="card_stats">
                <div class="key_number">
                <img src="assets/img/icons8-thermomètre-96.png" alt="">
                <?php
                    if( isset($_GET["date_debut"])&& isset($_GET["date_fin"])) {
                        $date_debut=$_GET["date_debut"];
                        $date_fin=$_GET["date_fin"];
                        $nom_zone="Genève, Schweiz/Suisse/Svizzera/Svizra";
                        $sql = "SELECT get_mean_temperature('$date_debut', '$date_fin','$nom_zone') as mean;";
                        $result = $conn->query($sql);

                        if ($result->num_rows > 0) {
                            // Récupérer la ligne de résultat
                            $row = $result->fetch_assoc();
                            // Récupérer la valeur de la colonne mean_temp (ou le nom de votre colonne)
                            $mean_temp = round($row['mean'],3);
                            // Afficher le résultat dans votre page HTML
                            echo "<p>$mean_temp</p>";
                        } else {
                            echo "Aucun résultat trouvé.";
                        }
                    }
                    ?>
                </div>
                <div class="details_key_number">° Celcius</div>
            </div>
        </div>
        <div id="graphs">
            <div class="card_graph">
                <?php
                echo "Moyenne de $parametre1 "
                ?>
                <div id="staticChart1">

                    <canvas id="myChart1"></canvas>
                </div>
            </div>
            <div class="card_graph">
            <?php
                echo "Moyenne de $parametre2 "
                ?>
                <div id="staticChart2">

                    <canvas id="myChart2"></canvas>
                </div>
            </div>
        </div>
        <div id="data_stats">
            <div class="card_data_stats">
                <div class="details_data">Date de collecte</div>
                <div class="data">

                    <?php
                    if( isset($_GET["date_debut"])) {
                        $date_debut=$_GET["date_debut"];
                        $date_fin=$_GET["date_fin"];
                        echo"<p>".$date_debut." => ". $date_fin."</p>";
                        }

                    ?>

                    <!--<img src="sunny.svg" alt="">-->
                </div>
            </div>
            <div class="card_data_stats">
                <div class="details_data">Nombre de points GPS </div>
                <div class="data">
                    <?php
                    if( isset($_GET["date_debut"])) {
                        $date_debut=$_GET["date_debut"];
                        $date_fin=$_GET["date_fin"];
                        $sql = "SELECT COUNT(DISTINCT idpoint) as num_points FROM 2026_solarx_mesures WHERE date_collecte BETWEEN '$date_debut' AND '$date_fin' ";
                        $result = $conn->query($sql);

                        if ($result->num_rows > 0) {
                            // Récupérer la ligne de résultat
                            $row = $result->fetch_assoc();
                            // Récupérer la valeur num_points
                            $num_points = $row['num_points'];
                            // Afficher le résultat dans votre page HTML
                            echo "<p>$num_points</p>";
                        } else {
                            echo "Aucun résultat trouvé.";
                        }
                    }

                    ?>
                    <!--<img src="sunny.svg" alt="">-->
                </div>
            </div>
            <div class="card_data_stats">
                <div class="details_data">Fiabilité des données</div>
                <div class="data">
                <?php
                    if( isset($_GET["date_debut"])) {
                        $date_debut=$_GET["date_debut"];
                        $date_fin=$_GET["date_fin"];
                        $sql = "SELECT COUNT(DISTINCT idpoint) as total_num_points FROM 2026_solarx_pointsgps;";
                        $result = $conn->query($sql);

                        if ($result->num_rows > 0) {
                            // Récupérer la ligne de résultat
                            $row = $result->fetch_assoc();
                            // Récupérer la valeur num_points
                            $total_num_points = $row['total_num_points'];
                            // Afficher le résultat dans votre page HTML
                            $fiabilite=intval($num_points/$total_num_points*100);
                            echo "<p>$fiabilite%</p>";
                        } else {
                            echo "Aucun résultat trouvé.";
                        }
                    }

                    ?>
                    <!--<img src="sunny.svg" alt="">-->
                </div>
            </div>
        </div>
    </main>

</body>

<script>
    document.getElementById('change_settings').addEventListener('click', function() {
        var asideElement = document.querySelector('aside');
        if (asideElement) {
            asideElement.classList.toggle('show_nav_bar_responsive');
            // Vérifier si la classe show_nav_bar_responsive est activée
            if (asideElement.classList.contains('show_nav_bar_responsive')) {
                // Si activée, cacher le défilement du body
                document.body.style.overflow = 'hidden';
            } else {
                // Sinon, rétablir le défilement du body
                document.body.style.overflow = '';
            }
        }
    });
</script>


<script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js"></script>
<script src="assets/js/dashboard.js"></script>
<script type="module" src="https://unpkg.com/ionicons@5.5.2/dist/ionicons/ionicons.esm.js"></script> <!-- Icônes Ionicons -->
<script nomodule src="https://unpkg.com/ionicons@5.5.2/dist/ionicons/ionicons.js"></script>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script src="./assets/js/chart1.js"></script>
</html>
