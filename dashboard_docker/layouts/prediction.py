from dash import html
import dash_bootstrap_components as dbc


def render_prediction():
    """
    Rendu de la page de prédiction (actuellement vide avec un titre)
    """
    return html.Div(
        style={
            "padding": "40px",
            "display": "flex",
            "justify-content": "center",
            "align-items": "center",
            "min-height": "80vh",
        },
        children=[
            html.Div(
                style={
                    "text-align": "center",
                },
                children=[
                    html.H1(
                        "PAGE DE PRÉDICTION",
                        style={
                            "font-size": "48px",
                            "font-weight": "bold",
                            "color": "#2c3e50",
                            "letter-spacing": "2px",
                            "margin-bottom": "20px",
                        },
                    ),
                    html.Hr(
                        style={
                            "width": "300px",
                            "margin": "0 auto",
                            "border": "2px solid #3498db",
                        }
                    ),
                    html.P(
                        "Prédictions basées sur l'IA - Bientôt disponible",
                        style={
                            "font-size": "18px",
                            "color": "#7f8c8d",
                            "margin-top": "20px",
                        },
                    ),
                ],
            )
        ],
    )