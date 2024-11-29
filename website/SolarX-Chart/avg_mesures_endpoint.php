<?php 

include('config_bdd.php');
$conn = new mysqli($servername, $username, $password, $database);

if ($conn->connect_error) {
    $msg = "erreur ". $conn->connect_error;
}

$host_info = mysqli_get_host_info($conn);

$server_info = mysqli_get_server_info($conn);


mysqli_query($conn, "SET NAMES UTF8");



$sql = "SELECT AVG(`mesures`.`precipitation`) as 'irra_temp',AVG(`mesures`.`temperature`) as 'moyen_temp', `mesures`.`date_collecte`
        FROM `mesures`
        group by `mesures`.`date_collecte`
        order by `mesures`.`date_collecte` ASC;";

$result = $conn->query($sql);
$data = $result->fetch_all(MYSQLI_ASSOC);
                   


// print_r($data); 
echo json_encode($data); 


?>