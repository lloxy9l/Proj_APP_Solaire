
let ctx = document.getElementById('myChart1');
let ctx1 = document.getElementById('myChart2');

let chart_temp = {
    type: 'line',
    data: {
      labels: [],
      datasets: [{
        label: '',
        data: [],
        borderWidth: 1
      }]
    },
    options: {
      scales: {
        y: {
          beginAtZero: true
        }
      }
    }
  };

  let chart_temp1 = {
    type: 'line',
    data: {
      labels: [],
      datasets: [{
        label: '',
        data: [],
        borderColor: 'rgb(75, 192, 192)',
        borderWidth: 1
      }]
    },
    options: {
      scales: {
        y: {
          beginAtZero: true
        }
      }
    }
  };

const myChart = new Chart(ctx, chart_temp);
const myChart1 = new Chart(ctx1, chart_temp1);


let xjs = new XMLHttpRequest();

let data = [];

const queryParams = new URLSearchParams(window.location.search);

// Étape 2: Accéder à un paramètre spécifique
const param1 = queryParams.get('parametre1'); 
const param2 = queryParams.get('parametre2');  // retournera "valeur1"
const param3 = queryParams.get('date_debut');  // retournera "valeur2"
const param4 = queryParams.get('date_fin');  // retournera "valeur2"

console.log(param1); // Affiche "valeur1"
console.log(param2); // Affiche "valeur2"
console.log(window.location.href);

console.log("https://tp-epua.univ-savoie.fr/~renandb/Site_web/Dashboard_web_new_design/Recup_chiffres_graphes.php?parametre1="+param1 +"&parametre2="+param2 +"&date_debut="+param3 +"&date_fin="+param4);

xjs.open("GET","https://tp-epua.univ-savoie.fr/~renandb/Site_web/Dashboard_web_new_design/Recup_chiffres_graphes.php?parametre1="+param1 +"&parametre2="+param2 +"&date_debut="+param3 +"&date_fin="+param4);
xjs.onreadystatechange = ()=>{
    if((xjs.readyState == 4) && (xjs.status == 200))
    {
        data = JSON.parse(xjs.response);

        configChart();

        myChart.update();
        myChart1.update();
    }
}
xjs.send();



function configChart()
{
    for (let mesure of data)
        {
            chart_temp.data.labels.push(mesure["date_collecte"]);
            chart_temp.data.datasets[0].data.push(mesure["moyen1"]);

            chart_temp1.data.labels.push(mesure["date_collecte"]);
            chart_temp1.data.datasets[0].data.push(mesure["moyen2"]);
            // chart_temp.data.datasets[1].data.push(mesure["irra_temp"]);
            // chart_temp.data.datasets[1].data.push(mesure["moyen_temp"]);
        }
}