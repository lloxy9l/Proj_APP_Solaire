from dash import html, dcc
import dash_bootstrap_components as dbc


def render_optimisation(fig_opt, top_points_table):
    return html.Div(
    style={
        "padding": "20px 80px 0 80px",
        "width": "100%",
    },
    children=[
        # Barre de recherche + profil (comme les autres pages)
        html.Div(
            style={
                "display": "flex",
                "justify-content": "space-between",
                "align-items": "center",
                "margin-bottom": "20px",
            },
            children=[
                html.Div(
                    style={"position": "relative", "width": "50%"},
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
                html.A(
                    href="/profile_content",
                    children=html.Img(
                        src="assets/img/profile.png",
                        style={
                            "width": "65px",
                            "height": "65px",
                            "border-radius": "50%",
                            "border": "2px solid #fff",
                        },
                    ),
                ),
            ],
        ),

        html.H1(
            "Optimisation du placement des panneaux solaires",
            style={"font-size": "36px", "margin-bottom": "20px"},
        ),

        # Grille : carte + top 10
        html.Div(
            style={
                "display": "grid",
                "grid-template-columns": "2fr 1fr",
                "gap": "20px",
                "margin-bottom": "20px",
            },
            children=[
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                dcc.Graph(
                                    id="graph-optimisation-map",
                                    figure=fig_opt,
                                    style={"width": "100%", "height": "650px"},
                                )
                            ]
                        )
                    ]
                ),
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                html.H4("Top 10 des meilleurs emplacements", style={"margin-bottom": "10px"}),
                                html.P(
                                    "Score global basé sur : ensoleillement, irradiance, production, précipitations et température.",
                                    style={"font-size": "13px"},
                                ),
                                top_points_table,
                            ]
                        )
                    ]
                ),
            ],
        ),

        html.Div(
            style={"margin-bottom": "30px"},
            children=[
                html.H5("Interprétation du score (0–100 %)"),
                html.Ul(
                    [
                        html.Li("Plus le score est élevé, plus le point est favorable à l'installation de panneaux solaires."),
                        html.Li("Les zones très ensoleillées et à forte irradiance/production sont privilégiées."),
                        html.Li("Les fortes précipitations et les écarts de température trop importants pénalisent le score."),
                    ],
                    style={"font-size": "13px"},
                ),
            ],
        ),
    ],
)

