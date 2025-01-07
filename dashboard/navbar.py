# navbar.py
from dash import html

def create_navbar():
    vertical_header_style = {
        "height": "100vh",
        "width": "80px",
        "background-color": "#005dff",
        "color": "white",
        "display": "flex",
        "flex-direction": "column",
        "justify-content": "space-between",
        "padding": "10px",
        "border-radius": "0 2em 2em 0",
        "transition": "width 0.3s ease",
        "overflow": "hidden",
        "position": "fixed",
        "z-index": "100"
    }

    vertical_header = html.Div(
        id="vertical-header",
        style=vertical_header_style,
        children=[
            html.Div(
                children=[
                    html.Img(
                        src="assets/img/logo.png",
                        style={"width": "60px", "border-radius": "8px", "margin-top": "10px"},
                    ),
                ]
            ),
            html.Div(
                id="nav-menu",
                style={
                    "display": "flex",
                    "flex-direction": "column",
                    "align-items": "flex-left",
                    "white-space": "nowrap",
                },
                children=[
                    html.A(
                        children=[
                            html.Img(
                                src="assets/img/home.png",
                                style={"width": "40px", "margin": "20px 10px", "vertical-align": "middle"},
                            ),
                            html.Span("Accueil", style={"margin-left": "10px", "font-size": "14px", "vertical-align": "middle", "display": "none"}),
                        ],
                        href="/home",
                    ),
                    html.A(
                        children=[
                            html.Img(
                                src="assets/img/sun.png",
                                style={"width": "40px", "margin": "20px 10px", "vertical-align": "middle"},
                            ),
                            html.Span("Ensoleillement", style={"margin-left": "10px", "font-size": "14px", "vertical-align": "middle", "display": "none"}),
                        ],
                        href="/ensoleillement",
                    ),
                    html.A(
                        children=[
                            html.Img(
                                src="assets/img/thermometer.png",
                                style={"width": "40px", "margin": "20px 10px", "vertical-align": "middle"},
                            ),
                            html.Span("Température", style={"margin-left": "10px", "font-size": "14px", "vertical-align": "middle", "display": "none"}),
                        ],
                        href="/temperature",
                    ),
                    html.A(
                        children=[
                            html.Img(
                                src="assets/img/rain.png",
                                style={"width": "40px", "margin": "20px 10px", "vertical-align": "middle"},
                            ),
                            html.Span("Précipitations", style={"margin-left": "10px", "font-size": "14px", "vertical-align": "middle", "display": "none"}),
                        ],
                        href="/precipitations",
                    ),
                    html.A(
                        children=[
                            html.Img(
                                src="assets/img/lightning.png",
                                style={"width": "40px", "margin": "20px 10px", "vertical-align": "middle"},
                            ),
                            html.Span("Electricité", style={"margin-left": "10px", "font-size": "14px", "vertical-align": "middle", "display": "none"}),
                        ],
                        href="/electricite",
                    ),
                ]
            ),
            html.Button(
                children=[
                    html.Img(
                        src="assets/img/arrow.png",
                        style={"width": "40px", "transition": "transform 0.3s"}
                    ),
                ],
                id="toggle-width-btn",
                style={"margin-top": "20px", "padding": "12px", "background-color": "#ffffff", "color": "#005dff", "border": "none", "cursor": "pointer", "border-radius": "2em"},
            ),
        ],
    )

    return vertical_header
