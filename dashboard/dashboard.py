import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import mysql.connector
from search import Search
import logging

# Configuração do logging
logging.basicConfig(level=logging.DEBUG)





# Instanciando a classe Search para interagir com o banco de dados
search_instance = Search(host="projet-idu.hqbr.win", user="dev", password="9e*s@@iCFNs#r8", database="projet_solarx")

# Initialisation de l'application Dash
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])



# Style général pour la barre latérale
vertical_header_style = {
    "height": "100vh",  # Prend toute la hauteur de l'écran
    "width": "80px",  # Largeur par défaut du header
    "background-color": "#005dff",  # Couleur de fond
    "color": "white",  # Couleur du texte
    "display": "flex",  # Flexbox pour l'alignement
    "flex-direction": "column",  # Alignement vertical
    "justify-content": "space-between",  # Espacement entre les sections
    "padding": "10px",
    "border-radius": "0 2em 2em 0",
    "transition": "width 0.3s ease",  # Animation pour le changement de largeur
    "overflow": "hidden",  # Masque le contenu qui dépasse
    "position":"fixed",
    "z-index":"100"
}

# Contenu du header vertical
vertical_header = html.Div(
    id="vertical-header",  # ID pour appliquer le style CSS au hover
    style=vertical_header_style,
    children=[
        # Logo ou titre
        html.Div(
            children=[
                html.Img(
                    src="assets/img/logo.png",
                    style={"width": "60px", "border-radius": "8px", "margin-top": "10px"},
                ),
            ]
        ),
        # Menu de navigation
        html.Div(
            id="nav-menu", # Ajout d'un ID pour manipuler les enfants dans le callback
            style={
                "display": "flex",
                "flex-direction": "column",  # Utilisation de flexbox pour aligner horizontalement
                "align-items": "flex-left",  # Alignement vertical au centre
                "white-space": "nowrap",  # Empêcher les retours à la ligne
            },
            children=[
                html.A(
                    children=[
                        html.Img(
                            src="assets/img/home.png",  # Icône pour Accueil
                            style={"width": "40px", "margin": "20px 10px", "vertical-align": "middle"},
                        ),
                        html.Span("Accueil", style={"margin-left": "10px", "font-size": "14px", "vertical-align": "middle", "display": "none"}),  # Span pour le texte
                    ],
                    href="/home",
                ),
                html.A(
                    children=[
                        html.Img(
                            src="assets/img/sun.png",  # Icône pour Rapports
                            style={"width": "40px", "margin": "20px 10px", "vertical-align": "middle"},
                        ),
                        html.Span("Ensoleillement", style={"margin-left": "10px", "font-size": "14px", "vertical-align": "middle", "display": "none"}),  # Span pour le texte
                    ],
                    href="/ensoleillement",
                ),
                html.A(
                    children=[
                        html.Img(
                            src="assets/img/thermometer.png",  # Icône pour Température
                            style={"width": "40px", "margin": "20px 10px", "vertical-align": "middle"},
                        ),
                        html.Span("Température", style={"margin-left": "10px", "font-size": "14px", "vertical-align": "middle", "display": "none"}),  # Span pour le texte
                    ],
                    href="/temperature",
                ),
                html.A(
                    children=[
                        html.Img(
                            src="assets/img/rain.png",  # Icône pour Paramètres
                            style={"width": "40px", "margin": "20px 10px", "vertical-align": "middle"},
                        ),
                        html.Span("Précipitations", style={"margin-left": "10px", "font-size": "14px", "vertical-align": "middle", "display": "none"}),  # Span pour le texte
                    ],
                    href="/precipitations",
                ),
                html.A(
                    children=[
                        html.Img(
                            src="assets/img/lightning.png",  # Icône pour Paramètres
                            style={"width": "40px", "margin": "20px 10px", "vertical-align": "middle"},
                        ),
                        html.Span("Electricité", style={"margin-left": "10px", "font-size": "14px", "vertical-align": "middle", "display": "none"}),  # Span pour le texte
                    ],
                    href="/electricite",
                ),
            ]
        ),
        
        # Bouton pour changer la taille
        html.Button(
            children=[
                html.Img(
                    src="assets/img/arrow.png",  # Icône de flèche
                    style={"width": "40px", "transition": "transform 0.3s"}  # Ajout de la transition de rotation
                ),
            ],
            id="toggle-width-btn",
            style={"margin-top": "20px", "padding": "12px", "background-color": "#ffffff", "color": "#005dff", "border": "none", "cursor": "pointer", "border-radius": "2em"},
        ),
    ],
)

# Contenu principal
main_content = html.Div(
    style={
        "margin-left": "80px",  # Décale le contenu principal à droite du header
        "padding": "20px 80px 0 80px",  # Ajoute un espace entre le header et le contenu principal
        "width": "100%",
    },
    
    children=[
        # Barre de recherche et photo de profil
        html.Div(
            style={
                "display": "flex",
                "justify-content": "space-between",  # Utilisation de space-between pour espacer les éléments
                "align-items": "center",  # Alignement vertical
                "margin-bottom": "20px",
            },
            children=[
                # Barre de recherche moderne
                html.Div(
                    style={
                        "position": "relative",  # Pour positionner l'icône à l'intérieur de l'input
                        "width": "50%",
                    },
                    children=[
                        html.Div(
                            style={
                                "position": "absolute",
                                "left": "10px",
                                "top": "50%",
                                "transform": "translateY(-50%)",
                            },
                            children=[
                                html.Img(
                                    id="search-icon", 
                                    src="assets/img/search-icon.png",
                                    style={"width": "30px", "height": "30px"},
                                ),
                            ],
                        ),
                        
                        

                        dcc.Input(
                            id="search-input",
                            type="text",
                            placeholder="Rechercher...",
                            style={
                                "width": "100%",
                                "padding": "10px 10px 10px 50px",
                                "border-radius": "2em",
                                "border": "2px solid #005DFF",
                                "background-color": "#f8f8f8",
                                "font-size": "18px",
                                "outline": "none",
                            },
                        ),

                       
                    ],
                ),
                    
                # Photo de profil
                html.A(
                    children=[
                    html.Img(src="assets/img/profile.png", alt="Profile Image")],
                    href="/profile", 
                        style={
                        "width": "65px",
                        "height": "65px",
                        "border-radius": "50%",
                        "border": "2px solid #fff",
                        "margin-right": "20px",
                        "margin-bottom": "15px",
                    },
                    id="profile-link", 
                ),
               # html.Div(id='page-content')  # Onde o conteúdo da página será exibido
            ],
        ),

          # Modal para exibir os resultados da pesquisa
                dbc.Modal(
                id="search-results-modal",
                is_open=False,  # Inicialmente fechado
                children=[
                    dbc.ModalHeader("Resultados da Pesquisa"),
                    dbc.ModalBody(
                        html.Div(
                            id="search-results-list",  # Lista para exibir os resultados
                            children=[],  # Inicialmente vazio
                        )
                    ),
                ],
            ),

       
        # Section des cartes pour les informations chiffrées
        html.Div(
            style={
                "display": "flex",
                "justify-content": "space-between",  # Utilisation de space-between pour espacer les éléments
                "align-items": "center",  # Alignement vertical
                "margin-bottom": "20px",
            },
            children=[
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                html.H4("Température", className="card-title"),
                                html.P("25°C", className="card-text"),
                            ]
                        ),
                    ],
                    style={"width": "18rem"},
                ),
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                html.H4("Précipitations", className="card-title"),
                                html.P("12 mm", className="card-text"),
                            ]
                        ),
                    ],
                    style={"width": "18rem"},
                ),
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                html.H4("Ensoleillement", className="card-title"),
                                html.P("8 h", className="card-text"),
                            ]
                        ),
                    ],
                    style={"width": "18rem"},
                ),
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                html.H4("Humidité", className="card-title"),
                                html.P("60%", className="card-text"),
                            ]
                        ),
                    ],
                    style={"width": "18rem"},
                ),
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                html.H4("Puissance éléctrique moyenne", className="card-title", style={"font-size": "17px"} ),
                                html.P("25 kW", className="card-text"),
                            ]
                        ),
                    ],
                    style={"width": "18rem","height": "6rem" },
                ),
            ],
        ),

        # Section des cartes pour les graphiques
        html.Div(
            style={
                "display": "grid",
                "grid-template-columns": "1fr 1fr",  # Grille 2x2
                "gap": "20px",  # Espace entre les cartes
            },
            children=[
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                dcc.Graph(
                                    id="graph-1",
                                    figure={
                                        "data": [
                                            {
                                                "x": [1, 2, 3, 4],
                                                "y": [10, 15, 13, 17],
                                                "type": "line",
                                                "name": "Température",
                                            }
                                        ],
                                        "layout": {"title": "Température"},
                                    },
                                )
                            ]
                        ),
                    ]
                ),
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                dcc.Graph(
                                    id="graph-2",
                                    figure={
                                        "data": [
                                            {
                                                "values": [50, 30, 20],
                                                "labels": ["Soleil", "Nuages", "Pluie"],
                                                "type": "pie",
                                            }
                                        ],
                                        "layout": {"title": "Météo"},
                                    },
                                )
                            ]
                        ),
                    ]
                ),
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                dcc.Graph(
                                    id="graph-3",
                                    figure={
                                        "data": [
                                            {
                                                "x": ["Lun", "Mar", "Mer", "Jeu", "Ven"],
                                                "y": [12, 19, 3, 5, 2],
                                                "type": "bar",
                                                "name": "Précipitations",
                                            }
                                        ],
                                        "layout": {"title": "Précipitations"},
                                    },
                                )
                            ]
                        ),
                    ]
                ),
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                dcc.Graph(
                                    id="graph-4",
                                    figure={
                                        "data": [
                                            {
                                                "x": [1, 2, 3, 4],
                                                "y": [3, 4, 5, 6],
                                                "type": "scatter",
                                                "mode": "markers",
                                                "name": "Points",
                                            }
                                        ],
                                        "layout": {"title": "Données diverses"},
                                    },
                                )
                            ]
                        ),
                    ]
                ),
            ],
        ),
        html.Div(id='results-container', style={"margin-top": "20px"})
    ],
)


# Disposition principale
app.layout = html.Div(
    style={"display": "flex"},
    children=[
        dcc.Store(id="sidebar-width", data="80px"),  # Stocker la largeur actuelle de la barre latérale
        vertical_header,
        main_content,
        dcc.Location(id='url', refresh=False),  
        html.A(
            children=html.Img(src="assets/img/profile.png", style={"width": "40px"}),
            href="/profile",  
        ),
        html.Div(id='page-content')  
    ],
)

# Callback pour changer la largeur de la barre latérale
@app.callback(
    [Output("vertical-header", "style"), Output("sidebar-width", "data"), Output("toggle-width-btn", "children")],
    Input("toggle-width-btn", "n_clicks"),
    State("sidebar-width", "data"),
    prevent_initial_call=True
)
def toggle_sidebar_width(n_clicks, current_width):
    new_width = "200px" if current_width == "80px" else "80px"
    updated_style = vertical_header_style.copy()
    updated_style["width"] = new_width

    # Gérer la rotation de la flèche
    rotate_style = {"transform": "rotate(180deg)"} if new_width == "200px" else {}

    # Mettre à jour les flèches et les spans
    new_children = [
        html.Img(
            src="assets/img/arrow.png",  # Icône de flèche
            style={**{"width": "40px"}, **rotate_style}  # Applique la rotation
        )
    ]

    return updated_style, new_width, new_children

# Callback pour gérer l'affichage des spans
@app.callback(
    Output("nav-menu", "children"),
    Input("sidebar-width", "data"),
    prevent_initial_call=True,
)
def update_menu_text_display(sidebar_width):
    # Si la largeur est réduite, on cache les spans
    if sidebar_width == "80px":
        # Retourne le menu avec les spans cachés
        return [
            html.A(
                children=[
                    html.Img(src="assets/img/home.png", style={"width": "40px", "margin": "20px 10px", "vertical-align": "middle"}),
                    html.Span("Accueil", style={"margin-left": "10px", "font-size": "14px", "vertical-align": "middle", "display": "none"}),
                ],
                href="#",
            ),
            html.A(
                children=[
                    html.Img(src="assets/img/sun.png", style={"width": "40px", "margin": "20px 10px", "vertical-align": "middle"}),
                    html.Span("Rapports", style={"margin-left": "10px", "font-size": "14px", "vertical-align": "middle", "display": "none"}),
                ],
                href="#",
            ),
            html.A(
                children=[
                    html.Img(src="assets/img/thermometer.png", style={"width": "40px", "margin": "20px 10px", "vertical-align": "middle"}),
                    html.Span("Température", style={"margin-left": "10px", "font-size": "14px", "vertical-align": "middle", "display": "none"}),
                ],
                href="#",
            ),
            html.A(
                children=[
                    html.Img(src="assets/img/rain.png", style={"width": "40px", "margin": "20px 10px", "vertical-align": "middle"}),
                    html.Span("Précipitations", style={"margin-left": "10px", "font-size": "14px", "vertical-align": "middle", "display": "none"}),
                ],
                href="#",
            ),
            html.A(
                children=[
                    html.Img(src="assets/img/lightning.png", style={"width": "40px", "margin": "20px 10px", "vertical-align": "middle"}),
                    html.Span("Electricité", style={"margin-left": "10px", "font-size": "14px", "vertical-align": "middle", "display": "none"}),
                ],
                href="#",
            ),
        ]
    else:
        # Si la largeur est agrandie, on montre les spans
        return [
            html.A(
                children=[
                    html.Img(src="assets/img/home.png", style={"width": "40px", "margin": "20px 10px", "vertical-align": "middle"}),
                    html.Span("Accueil", style={"margin-left": "10px", "font-size": "18px", "vertical-align": "middle", "display": "inline", "color": "#fff", "font-size": "16px", "outline": "none"}),
                ],
                href="#",
            ),
            html.A(
                children=[
                    html.Img(src="assets/img/sun.png", style={"width": "40px", "margin": "20px 10px", "vertical-align": "middle"}),
                    html.Span("Ensoleillement", style={"margin-left": "10px", "font-size": "18px", "vertical-align": "middle", "display": "inline", "color": "#fff", "font-size": "16px", "outline": "none"}),
                ],
                href="#",
            ),
            html.A(
                children=[
                    html.Img(src="assets/img/thermometer.png", style={"width": "40px", "margin": "20px 10px", "vertical-align": "middle"}),
                    html.Span("Température", style={"margin-left": "10px", "font-size": "18px", "vertical-align": "middle", "display": "inline", "color": "#fff", "font-size": "16px", "outline": "none"}),
                ],
                href="#",
            ),
            html.A(
                children=[
                    html.Img(src="assets/img/rain.png", style={"width": "40px", "margin": "20px 10px", "vertical-align": "middle"}),
                    html.Span("Précipitations", style={"margin-left": "10px", "font-size": "18px", "vertical-align": "middle", "display": "inline", "color": "#fff", "font-size": "16px", "outline": "none"}),
                ],
                href="#",
            ),
            html.A(
                children=[
                    html.Img(src="assets/img/lightning.png", style={"width": "40px", "margin": "20px 10px", "vertical-align": "middle"}),
                    html.Span("Electricité", style={"margin-left": "10px", "font-size": "18px", "vertical-align": "middle", "display": "inline", "color": "#fff", "font-size": "16px", "outline": "none"}),
                ],
                href="#",
            ),
        ]


 # Callback para realizar a pesquisa e exibir os resultados ao pressionar Enter
@app.callback(
    [Output("search-results-modal", "is_open"),  # Controla a abertura/fechamento do modal
     Output("search-results-list", "children")],  # Exibe os resultados na lista do modal
    Input("search-input", "value")  # O callback será acionado quando o valor do input mudar
)
def update_search_results(search_term):
    # Teste para verificar o valor digitado
    logging.debug(f"Valor digitado: {search_term}")

    # Verifica se o campo de pesquisa está vazio
    if not search_term:
        logging.debug("Campo vazio. Fechando o modal.")
        return False, []  # Fecha o modal e não exibe resultados

    # Realizando a busca no banco de dados
    try:
        logging.debug("Iniciando a busca no banco de dados...")
        results = search_instance.search_in_all_tables(search_term)
        logging.debug(f"Resultados encontrados: {results}")

    except Exception as e:
        logging.error(f"Erro durante a busca: {str(e)}")
        return [{"error": str(e)}]

    # Formatando os resultados para exibição no pop-up
    if results:
        results_list = [html.Div(f"Resultado {i+1}: {result[0]}") for i, result in enumerate(results)]
        return True, results_list  # Abre o modal e exibe os resultados
    else:
        logging.debug("Nenhum resultado encontrado.")
        return True, [html.Div("Nenhum resultado encontrado")]  # Exibe a mensagem de nenhum resultado encontrado
    

@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')  # Observa o pathname da URL
)
def display_page(pathname):
    if pathname == '/profile':
        return None
    else: 
        return None

# Exécution de l'application
if __name__ == "__main__":
    app.run_server(debug=True)



