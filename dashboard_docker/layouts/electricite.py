from dash import html, dcc
import dash_bootstrap_components as dbc


def render_electricite(fig_ratio, figure_pie):
    return html.Div(
    style={
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
                    href="/profile_content",  # Remplacez par le lien voulu
                    children=html.Img(
                        src="assets/img/profile.png",
                        style={
                            "width": "65px",
                            "height": "65px",
                            "border-radius": "50%",
                            "border": "2px solid #fff",
                        },
                    )
                ),
            ],
        ),
        html.H1(
            "Electricité",  # Nom de la page
            style={
                "font-size": "36px",  # Taille de la police
                "margin-bottom": "20px",  # Espace en dessous du titre
            },
        ),        # Section des cartes pour les graphiques en 3x3
        html.Div(
            style={
                "display": "grid",
                "grid-template-columns": "1fr",  # 1 seule colonne sur la première ligne
                "gap": "20px",  # Espace entre les cartes
            },
            children = [
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                dcc.Graph(
                                    id='map-graph',
                                    
                                    style={
                                        'height': 'calc(100vh - 350px)',
                                        'width': '100%'
                                    }
                                ),
                                html.Div(
                                    id='click-data',
                                    style={
                                        'padding': '5px',
                                        'font-size': '20px'
                                    }
                                )
                            ]
                        ),
                    ]
                ),
            ]

        ),
        # Deuxième ligne - 3 colonnes
        html.Div(
            style={
                "display": "grid",
                "grid-template-columns": "repeat(2, 1fr)",  # 3 colonnes
                "gap": "20px",  # Espacement entre les cartes
                "margin-top": "20px",
            },
            children=[
                # Deuxième carte
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                dcc.Graph(
                                    id="graph-2",
                                    figure=figure_pie,
                                )
                            ]
                        ),
                    ]
                ),
                
                # Troisième carte
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                dcc.Graph(
                                    id="graph-3",
                                    figure=fig_ratio.update_layout(
                                        plot_bgcolor='white',  # Fond du graphique en blanc
                                        paper_bgcolor='white',  # Fond extérieur en blanc
                                        title={
                                        "font": {"size": 22,},  # Taille et gras du titre
                                        "x": 0.5,  # Centrer le titre horizontalement
                                        }
                                    )
                                )
                            ]
                        ),
                    ]
                ),
            ],
        ),
    ],
)

