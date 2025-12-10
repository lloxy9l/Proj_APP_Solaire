from dash import html, dcc


def render_credit():
    return html.Div(
    style={
        "margin-left": "80px",
        "padding": "20px",
        "display": "flex",
        "justify-content": "center",
        "align-items": "center",
        "height": "810px",
        "width": "917px",
        "background-color": "#005dff",
        "border-radius": "30px",
        "position": "absolute",
        "top": "50%",
        "left": "50%",
        "transform": "translate(-50%, -50%)",
    },
    children=[
        html.Div(
            style={
                "background-color": "white",
                "padding": "30px",
                "border-radius": "10px",
                "width": "800px",
                "height": "705px",
                "box-shadow": "0 4px 6px rgba(0, 0, 0, 0.1)"
            },
            children=[
                # Titre de la page
                html.Div(
                    style={"text-align": "center", "margin-bottom": "20px"},
                    children=[
                        html.H1("Geneva Weather Data Collection", style={"color": "#005dff"}),
                        html.P(
                            "Projet réalisé par un groupe d'étudiants pour collecter et analyser les données météorologiques de la région de Genève.",
                            style={"color": "#555"}
                        )
                    ]
                ),

                # Description du projet
                html.Div(
                    style={"margin-bottom": "20px"},
                    children=[
                        html.H2("Introduction", style={"color": "#005dff"}),
                        html.P(
                            "Ce projet vise à collecter des données météorologiques détaillées et fiables pour la région de Genève. Ces données sont essentielles pour des applications comme la planification urbaine, l'agriculture, et les projets d'énergie renouvelable."
                        ),
                        html.H2("Objectifs", style={"color": "#005dff"}),
                        html.Ul([
                            html.Li("Collecter des données sur la luminosité, la radiance, la température et les précipitations."),
                            html.Li("Fournir des informations exploitables pour les parties prenantes locales."),
                            html.Li("Créer une base de données robuste pour le stockage sécurisé des données.")
                        ])
                    ]
                ),

                # Liste des membres de l'équipe
                html.Div(
                    style={"margin-bottom": "20px"},
                    children=[
                        html.H2("Équipe", style={"color": "#005dff"}),
                        html.Ul([
                            html.Li("Maxens Soldan"),
                            html.Li("Baptiste Renand"),
                            html.Li("Arno Wilhelm"),
                            html.Li("Degouey Corentin"),
                            html.Li("Hassnaoui Walid"),
                            html.Li("Bercier Thomas"),
                            html.Li("Francielle Andrade Cardoso")
                        ]),
                        html.P("Coryright 2025")
                    ]
                ),
            ]
        )
    ]
)

