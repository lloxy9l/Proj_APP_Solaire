from dash import html, dcc
import dash_bootstrap_components as dbc


def render_optimisation(fig_opt, top_points_data, map_optimisation):
    return html.Div(
        style={
            "padding": "20px 80px 0 80px",
            "width": "100%",
        },
        children=[
            
            # Titre + sous-titre
            html.Div(
                style={"margin-bottom": "10px"},
                children=[
                    html.H1(
                        "Optimisation du placement des panneaux solaires",
                        style={
                            "font-size": "36px",
                            "margin-bottom": "6px",
                        },
                    ),
                    html.P(
                        "Carte d'optimalité combinant ensoleillement, irradiance, production, précipitations et température "
                        "pour prioriser les emplacements les plus favorables.",
                        style={
                            "font-size": "14px",
                            "color": "#555",
                            "max-width": "900px",
                        },
                    ),
                ],
            ),

            # Grille : carte + top 5
            html.Div(
                style={
                    "display": "grid",
                    "grid-template-columns": "2fr 1fr",
                    "gap": "20px",
                    "margin-bottom": "24px",
                },
                children=[
                    # Carte Leaflet interactive (HTML embarqué)
                    dbc.Card(
                        style={
                            "border-radius": "18px",
                            "overflow": "hidden",
                            "box-shadow": "0 10px 24px rgba(0, 0, 0, 0.08)",
                            "border": "1px solid #e3ebff",
                        },
                        children=[
                            dbc.CardBody(
                                style={"padding": 0},
                                children=[
                                    html.Iframe(
                                        id="optimisation-map",
                                        srcDoc=map_optimisation,
                                        style={
                                            "width": "100%",
                                            "height": "650px",
                                            "border": "none",
                                        },
                                    )
                                ],
                            )
                        ],
                    ),
                    # Top 5 des meilleurs emplacements
                    dbc.Card(
                        style={
                            "border-radius": "18px",
                            "box-shadow": "0 10px 24px rgba(0, 0, 0, 0.06)",
                            "border": "1px solid #e6ecff",
                        },
                        children=[
                            dbc.CardBody(
                                children=[
                                    html.H4(
                                        "Top 5 des meilleurs emplacements",
                                        style={
                                            "margin-bottom": "8px",
                                            "font-size": "20px",
                                        },
                                    ),
                                    html.P(
                                        "Les points ci-dessous présentent les scores globaux les plus élevés sur l'ensemble du territoire.",
                                        style={
                                            "font-size": "13px",
                                            "color": "#666",
                                            "margin-bottom": "8px",
                                        },
                                    ),
                                    html.Div(
                                        style={
                                            "display": "flex",
                                            "justify-content": "space-between",
                                            "align-items": "center",
                                            "margin-bottom": "4px",
                                        },
                                        children=[
                                            html.Span(
                                                "Filtrer par score minimum",
                                                style={"font-size": "12px", "color": "#555"},
                                            ),
                                            html.Span(
                                                id="opt-score-label",
                                                style={"font-size": "12px", "font-weight": "600", "color": "#005DFF"},
                                            ),
                                        ],
                                    ),
                                    dcc.Slider(
                                        id="opt-score-slider",
                                        min=0,
                                        max=100,
                                        step=1,
                                        value=60,
                                        updatemode="drag",
                                    ),
                                    dcc.Store(
                                        id="opt-top-points-data",
                                        data=top_points_data,
                                    ),
                                    html.Div(
                                        id="opt-top-points-list",
                                        style={"margin-top": "12px"},
                                    ),
                                ]
                            )
                        ],
                    ),
                ],
            ),

            # Bloc d'interprétation du score
            dbc.Card(
                style={
                    "margin-bottom": "30px",
                    "border-radius": "18px",
                    "border": "1px solid #dbe9ff",
                    "background": "linear-gradient(135deg, #f7fbff 0%, #ffffff 55%, #f3f6ff 100%)",
                    "box-shadow": "0 8px 18px rgba(0, 42, 120, 0.08)",
                },
                children=[
                    dbc.CardBody(
                        children=[
                            html.Div(
                                style={
                                    "display": "flex",
                                    "align-items": "center",
                                    "margin-bottom": "10px",
                                },
                                children=[
                                    html.Div(
                                        "i",
                                        style={
                                            "width": "22px",
                                            "height": "22px",
                                            "border-radius": "50%",
                                            "background-color": "#005DFF",
                                            "color": "white",
                                            "display": "flex",
                                            "align-items": "center",
                                            "justify-content": "center",
                                            "font-size": "14px",
                                            "margin-right": "8px",
                                        },
                                    ),
                                    html.H5(
                                        "Interprétation du score global (0–100 %)",
                                        style={
                                            "margin": 0,
                                            "font-size": "16px",
                                        },
                                    ),
                                ],
                            ),
                            html.P(
                                "Chaque point GPS reçoit un score synthétique calculé à partir de cinq indicateurs météo et "
                                "énergétiques. Ce score sert à comparer rapidement le potentiel d'installation de panneaux solaires "
                                "entre différentes zones.",
                                style={
                                    "font-size": "13px",
                                    "color": "#555",
                                    "margin-bottom": "12px",
                                },
                            ),
                            html.Div(
                                style={
                                    "display": "grid",
                                    "grid-template-columns": "1fr 1fr",
                                    "gap": "10px",
                                    "font-size": "13px",
                                },
                                children=[
                                    html.Ul(
                                        children=[
                                            html.Li("Score > 85 % : zone prioritaire, très bon potentiel solaire."),
                                            html.Li("Score entre 70 % et 85 % : bon compromis entre production et contraintes météo."),
                                            html.Li("Score entre 50 % et 70 % : potentiel correct mais à analyser avec le terrain (ombrage, accès, etc.)."),
                                            html.Li("Score < 50 % : zone moins intéressante pour une installation photovoltaïque massive."),
                                        ]
                                    ),
                                    html.Ul(
                                        children=[
                                            html.Li("Ensoleillement, irradiance et production tirent le score vers le haut."),
                                            html.Li("Les fortes précipitations et les écarts importants à 20 °C réduisent le score."),
                                            html.Li("Les pondérations peuvent être ajustées selon la stratégie (maximiser la production, limiter les risques météo...)."),
                                            html.Li("La carte interactive permet de visualiser spatialement ces différences de potentiel."),
                                        ]
                                    ),
                                ],
                            ),
                        ]
                    )
                ],
            ),
        ],
    )
