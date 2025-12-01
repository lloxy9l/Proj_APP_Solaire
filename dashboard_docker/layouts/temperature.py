from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.express as px


def render_temperature(df_mois, fig_temp, map_temperature):
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
            ],
        ),
        html.H1(
            "Temperature",  # Nom de la page
            style={
                "font-size": "36px",  # Taille de la police
                "margin-bottom": "20px",  # Espace en dessous du titre
            },
        ),
        
        # Section des cartes pour les graphiques - 1 seule colonne pour la première ligne, 3 colonnes pour la deuxième ligne
        html.Div(
            style={
                "display": "grid",
                "grid-template-columns": "1fr",  # 1 seule colonne sur la première ligne
                "gap": "20px",  # Espacement entre les cartes
            },
            children=[
                # Première carte (ligne 1)
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                               html.Iframe(srcDoc=map_temperature, width='100%', height='800px')
                            ]
                        ),
                    ]
                ),
            ],
        ),
        
        # Deuxième ligne - 3 colonnes
        html.Div(
            style={
                "display": "grid",
                "grid-template-columns": "repeat(2, 1fr)",  # 2 colonnes
                "gap": "20px",  # Espacement entre les cartes
                "margin-top":"20px",
                "height":"50vh"
            },
            children=[
                # Deuxième carte
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                dcc.Graph(
                                    id="graph-2",
                                    
                                    figure=fig_temp,
                                    style={"width": "100%", "height": "100%"},
                                ),
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
                                    figure = px.bar(
                                        df_mois,
                                        x="mois",
                                        y="temperature",
                                        title="Distribution des temperature par mois",
                                        labels={"temperature": "Temperature en °C", "mois": "Mois"},
                                        color="temperature",  # Utilisation d'une échelle de couleur pour la temperature
                                        color_continuous_scale="Plasma",
                                    ).update_layout(
                                        plot_bgcolor='white',  # Fond du graphique en blanc
                                        paper_bgcolor='white',  # Fond extérieur en blanc
                                        title={
                                        "font": {"size": 22,},  # Taille et gras du titre
                                        "x": 0.5,  # Centrer le titre horizontalement
                                    }
                                    ),
                                    style={"width": "100%", "height": "100%"},
                                )
                            ]
                        ),
                    ]
                ),
            ],
        ),
    ],
)

