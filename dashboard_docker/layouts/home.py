from dash import html, dcc
import dash_bootstrap_components as dbc


def render_main_content(global_means, map_production):
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
                                html.P("Température", className="card-title"),
                                html.H4(f"{global_means['temperature']:.2f}°C/jour", className="card-text"),
                            ]
                        ),
                    ],
                    style={"width": "18rem"},
                ),
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                html.P("Précipitations", className="card-title"),
                                html.H4(f"{global_means['precipitation']:.2f} mm/jour", className="card-text"),
                            ]
                        ),
                    ],
                    style={"width": "18rem"},
                ),
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                html.P("Ensoleillement", className="card-title"),
                                html.H4(f"{global_means['ensoleillement']:.2f} heures/jour", className="card-text"),
                            ]
                        ),
                    ],
                    style={"width": "18rem"},
                ),
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                html.P("Irradiance", className="card-title"),
                                html.H4(f"{global_means['irradiance']:.2f} W/m²/jour", className="card-text"),
                            ]
                        ),
                    ],
                    style={"width": "18rem"},
                ),
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                html.P("Consommation éléctrique moyenne", className="card-title"),
                                html.H4(f"{global_means['consommation']:.2f} GWh/année", className="card-text"),
                            ]
                        ),
                    ],
                ),
            ],
        ),

        # Section des cartes pour les graphiques
        html.Div(
            style={
                "width":"100%",
                "height":"calc(100vh-350px)",
            },
            children=[
                # Première ligne - 1 colonne
                dbc.Card(
                [
                    dbc.CardBody(
                        [
                            html.Iframe(id='map-production-iframe', srcDoc=map_production, width='100%', height='800px')
                        ]
                    ),
                ]
                ),
            ],
        ),
    ],
)
