import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc

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
                    src="assets/logo.png",
                    style={"width": "100%", "border-radius": "8px", "margin-top": "10px"},
                ),
            ]
        ),
        # Menu de navigation
        html.Div(
            children=[
                html.A(
                    children=[
                        html.Img(
                            src="assets/home.png",  # Icône pour Accueil
                            style={"width": "60%", "margin": "20px 10px", "vertical-align": "middle"},
                        ),
                    ],
                    href="#",
                ),
                html.A(
                    children=[
                        html.Img(
                            src="assets/sun.png",  # Icône pour Rapports
                            style={"width": "60%", "margin": "20px 10px", "vertical-align": "middle"},
                        ),
                    ],
                    href="#",
                ),
                html.A(
                    children=[
                        html.Img(
                            src="assets/thermometer.png",  # Icône pour Rapports
                            style={"width": "60%", "margin": "20px 10px", "vertical-align": "middle"},
                        ),
                    ],
                    href="#",
                ),
                html.A(
                    children=[
                        html.Img(
                            src="assets/rain.png",  # Icône pour Paramètres
                            style={"width": "60%", "margin": "20px 10px", "vertical-align": "middle"},
                        ),
                    ],
                    href="#",
                ),
            ]
        ),
        # Pied de page
        html.Div(
            style={
                "display": "flex",  # Utilise Flexbox
                "justify-content": "center",  # Centre horizontalement
                "align-items": "center",  # Centre verticalement
            },
            children=[
                html.A(  # Lien autour de l'image
                    href="#",  # URL cible
                    target="_blank",  # Ouvre le lien dans un nouvel onglet
                    children=[
                        html.Img(
                            src="assets/log-out.png",
                            style={"width": "60%", "border-radius": "8px", "margin-left": "10px", "margin-bottom": "10px"},
                        ),
                    ],
                ),
            ],
        ),
        # Bouton pour changer la taille
        html.Button("Toggle Width", id="toggle-width-btn", style={"margin-top": "20px", "background-color": "#ffffff", "color": "#005dff", "border": "none", "cursor": "pointer"}),
    ],
)

# Contenu principal
main_content = html.Div(
    style={
        "margin-left": "80px",  # Décale le contenu principal à droite du header
        "padding": "20px",
    },
    children=[
        html.H1("Bienvenue dans le Dashboard"),
        html.P("Voici un exemple de contenu principal."),
    ],
)

# Disposition principale
app.layout = html.Div(
    style={"display": "flex"},
    children=[
        dcc.Store(id="sidebar-width", data="80px"),  # Stocker la largeur actuelle de la barre latérale
        vertical_header,
        main_content,
    ],
)

# Callback pour changer la largeur de la barre latérale
@app.callback(
    Output("vertical-header", "style"),
    Input("toggle-width-btn", "n_clicks"),
    State("sidebar-width", "data"),
    prevent_initial_call=True
)
def toggle_sidebar_width(n_clicks, current_width):
    new_width = "400px" if current_width == "80px" else "80px"
    vertical_header_style["width"] = new_width
    return vertical_header_style

# Exécution de l'application
if __name__ == "__main__":
    app.run_server(debug=True)