


let ctx = document.getElementById('myChart');

let chart_temp = {
    type: 'line',
    data: {
      labels: [],
      datasets: [{
        label: 'Temp. moy. par date',
        data: [],
        borderWidth: 1
      },{
        label: 'Irr. moy. par annee',
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

const myChart = new Chart(ctx, chart_temp);


let xjs = new XMLHttpRequest();

let data = [];

//  --- set all countries into aside --
xjs.open("GET","http://localhost/ChartSolarX/avg_mesures_endpoint.php");
xjs.onreadystatechange = ()=>{
    if((xjs.readyState == 4) && (xjs.status == 200))
    {
        data = JSON.parse(xjs.response);

        configChart();

        myChart.update();
    }
}
xjs.send();



function configChart()
{
    for (let mesure of data)
        {
            chart_temp.data.labels.push(mesure["date_collecte"]);
            chart_temp.data.datasets[0].data.push(mesure["moyen_temp"]);
            chart_temp.data.datasets[1].data.push(mesure["irra_temp"]);
            // chart_temp.data.datasets[1].data.push(mesure["moyen_temp"]);
        }
}