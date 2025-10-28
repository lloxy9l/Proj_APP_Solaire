var input = document.querySelector('#searchbarcontainer input[type="text"]');
var searchBarContainer = document.querySelector('#searchbarcontainer');

input.addEventListener('focus', function() {
    searchBarContainer.style.borderColor = '#3498db';
    searchBarContainer.style.boxShadow = '0 0 10px rgba(52, 152, 219, 0.5)';
});

input.addEventListener('blur', function() {
    searchBarContainer.style.borderColor = '#ccc';
    searchBarContainer.style.boxShadow = 'none';
});

searchBarContainer.addEventListener('mouseenter', function() {
    searchBarContainer.style.borderColor = '#ccc';
    searchBarContainer.style.boxShadow = 'none';
});

input.addEventListener('mouseenter', function() {
    searchBarContainer.style.borderColor = '#3498db';
    searchBarContainer.style.boxShadow = '0 0 10px rgba(52, 152, 219, 0.5)';
});

input.addEventListener('mouseleave', function() {
    if (!input.matches(':focus')) {
        searchBarContainer.style.borderColor = '#ccc';
        searchBarContainer.style.boxShadow = 'none';
    }
});

$(document).ready(function(){
    $('#nom_zone').on('input', function(){
        var searchTerm = $(this).val();
        if (searchTerm.length >= 1) {
            $.ajax({
                url: 'assets/php/search.php',
                type: 'GET',
                data: {query: searchTerm},
                success: function(response){
                    $('#resultcontainer').html(response);
                    document.querySelector('#resultcontainer').style.display = "block";
                }
            });
        } else {
            $('#resultcontainer').empty();
            document.querySelector('#resultcontainer').style.display = "none";
        }
    });
});