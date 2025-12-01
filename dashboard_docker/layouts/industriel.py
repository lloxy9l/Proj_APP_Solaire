from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.express as px


def render_zones_industrielles(map_zones_industrielles, zones_df):
    
    # Figures préparées comme avant
    fig_hist = px.histogram(
        zones_df,
        x="niveau_adaptabilite",
        title="Distribution des zones par niveau d'adaptabilité",
        color="niveau_adaptabilite",
        color_discrete_map={
            "Adaptée": "#2ecc71",
            "Moyenne": "#f39c12",
            "Non adaptée": "#e74c3c"
        }
    ).update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        title={"font": {"size": 22}, "x": 0.5},
        xaxis_title="Niveau d'adaptabilité",
        yaxis_title="Nombre de zones"
    )

    top10 = zones_df.nlargest(10, "production_potentielle") if len(zones_df) >= 10 else zones_df
    fig_bar = px.bar(
        top10,
        x="name",
        y="production_potentielle",
        title="Top 10 des zones à plus fort potentiel de production",
        color="production_potentielle",
        color_continuous_scale="Greens"
    ).update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        title={"font": {"size": 22}, "x": 0.5},
        xaxis_title="Zone",
        yaxis_title="Production potentielle (MWh/an)"
    )

    return html.Div(
        style={
            "padding": "20px 80px 0 80px",
            "width": "100%",
        },
        children=[

            # ------------------------------------------------------
            # 🔍 Barre de recherche + Profil (identique à electricité)
            # ------------------------------------------------------
            html.Div(
                style={
                    "display": "flex",
                    "justify-content": "space-between",
                    "align-items": "center",
                    "margin-bottom": "20px",
                },
                children=[
                    # Barre de recherche
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

                ],
            ),

            # ------------------------------------------------------
            # 🏷️ Titre
            # ------------------------------------------------------
            html.H1(
                "Zones Industrielles - Potentiel Solaire",
                style={"font-size": "36px", "margin-bottom": "20px"},
            ),

            # ------------------------------------------------------
            # 🗺️ Carte (1 colonne)
            # ------------------------------------------------------
            html.Div(
                style={
                    "display": "grid",
                    "grid-template-columns": "1fr",
                    "gap": "20px",
                },
                children=[
                    dbc.Card([
                        dbc.CardBody([
                            html.Iframe(
                                srcDoc=map_zones_industrielles,
                                width="100%",
                                height="800px",
                                style={"border": "none"}
                            )
                        ])
                    ])
                ]
            ),

            # ------------------------------------------------------
            # 📊 Deux graphiques (2 colonnes)
            # ------------------------------------------------------
            html.Div(
                style={
                    "display": "grid",
                    "grid-template-columns": "repeat(2, 1fr)",
                    "gap": "20px",
                    "margin-top": "20px",
                    "margin-bottom": "20px",
                    "height": "50vh",
                },
                children=[
                    # Histogramme
                    dbc.Card([
                        dbc.CardBody([
                            dcc.Graph(
                                id="zones-distribution",
                                figure=fig_hist,
                                style={"width": "100%", "height": "100%"}
                            )
                        ])
                    ]),

                    # Bar chart
                    dbc.Card([
                        dbc.CardBody([
                            dcc.Graph(
                                id="zones-production",
                                figure=fig_bar,
                                style={"width": "100%", "height": "100%"}
                            )
                        ])
                    ])
                ]
            ),
        ]
    )