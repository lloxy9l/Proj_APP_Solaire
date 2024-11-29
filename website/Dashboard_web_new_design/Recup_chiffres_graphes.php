<?php

    include('config_bdd.php');
    $conn = new mysqli($servername, $username, $password, $database);

    if ($conn->connect_error) {
        $msg = "erreur ". $conn->connect_error;
    }

    $host_info = mysqli_get_host_info($conn);

    $server_info = mysqli_get_server_info($conn);


    mysqli_query($conn, "SET NAMES UTF8");

    $type1 = $_GET["parametre1"];
    $type2 = $_GET["parametre2"];
    $data_debut = $_GET["date_debut"];
    $data_fin = $_GET["date_fin"];




    $sql = "SELECT AVG(2026_solarx_mesures.$type1) as 'moyen1',AVG(2026_solarx_mesures.$type2) as 'moyen2', DATE_FORMAT(2026_solarx_mesures.date_collecte, '%m %d %Y') as 'date_collecte'
    FROM 2026_solarx_mesures
    WHERE date_collecte BETWEEN '$data_debut' AND '$data_fin'
    group by 2026_solarx_mesures.date_collecte
    order by 2026_solarx_mesures.date_collecte ASC;";


    // print($sql);

    $result = $conn->query($sql);
    $data = $result->fetch_all(MYSQLI_ASSOC);



    // print_r($data);
    echo json_encode($data);


?>
