<?php

include "../../config_bdd.php";
$conn = new mysqli($servername, $username, $password, $database);

// Récupère la valeur de recherche
$searchTerm = $_GET['query'];

// Prépare et exécute la requête SQL
$sql = "SELECT nom FROM zone WHERE nom LIKE '%$searchTerm%'";
$result = $conn->query($sql);

// Affiche les résultats
if ($result->num_rows > 0) {
    while($row = $result->fetch_assoc()) {
        echo "<div>" . $row["nom"] . "</div>";
    }
} else {
    echo "Aucun résultat trouvé";
}

$conn->close();
?>