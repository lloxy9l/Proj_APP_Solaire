import dash
from dash import html, dcc
from dash import Input, Output, State
import dash_bootstrap_components as dbc

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Estilo do cabeçalho vertical
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
}

# Cabeçalho vertical
vertical_header = html.Div(
    id="vertical-header",
    style=vertical_header_style,
    children=[
        html.Div(
            children=[
                html.Img(
                    src="assets/logo.png",
                    style={"width": "100%", "border-radius": "8px", "margin-top": "10px"},
                ),
            ]
        ),
        html.Div(
            children=[
                html.A(
                    children=[
                        html.Img(
                            src="assets/home.png",
                            style={"width": "60%", "margin": "20px 10px"},
                        ),
                    ],
                    href="#",
                    id="link-home",
                ),
                html.A(
                    children=[
                        html.Img(
                            src="assets/user.png",
                            style={"width": "60%", "margin": "20px 10px"},
                        ),
                    ],
                    href="#",
                    id="link-profile",
                ),
            ]
        ),
        html.Div(
            style={"display": "flex", "justify-content": "center", "align-items": "center"},
            children=[
                html.A(
                    href="#",
                    target="_blank",
                    children=[
                        html.Img(
                            src="assets/log-out.png",
                            style={"width": "60%", "border-radius": "8px", "margin-left": "10px", "margin-bottom": "10px"},
                        ),
                    ],
                ),
            ],
        ),
    ],
)

# Conteúdo da página de perfil
profile_page_content = html.Div(
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
                # Título e imagem do usuário
                html.Div(
                    style={"margin-top": "10px"},
                    children=[
                        html.Div(
                            style={"display": "flex", "align-items": "center"},
                            children=[
                                # Imagem do usuário
                                html.Div(
                                    style={
                                        "position": "relative",
                                        "width": "120px",
                                        "height": "120px",
                                        "border-radius": "50%",
                                        "background-image": "url('assets/img/user_image.png')",
                                        "background-size": "cover",
                                        "background-position": "center",
                                        "border": "3px solid white",
                                    },
                                    children=[
                                        # Ícone de editar imagem
                                        html.Div(
                                            style={
                                                "position": "absolute",
                                                "bottom": "5px",
                                                "right": "5px",
                                                "background-color": "#005dff",
                                                "border-radius": "50%",
                                                "padding": "5px",
                                                "background-image": "url('assets/svg/edit.svg')",
                                            },
                                            children=[
                                                html.Img(
                                                    src="assets/edit-icon.png",
                                                    style={"width": "20px", "height": "20px"},
                                                ),
                                            ],
                                        ),
                                    ],
                                ),
                                # Nome e email do usuário
                                html.Div(
                                    style={"margin-left": "15px"},
                                    children=[
                                        html.H3("User Name", style={"margin-bottom": "5px"}),
                                        html.P("useremail@example.com", style={"color": "#888"}),
                                    ]
                                ),
                            ]
                        ),
                    ]
                ),
                html.Hr(style={"border": "none", "border-top": "1px solid #ddd", "box-shadow": "0 2px 4px rgba(0, 0, 0, 0.1)", "margin": "5px 0"}),

                # Detalhes do usuário
                html.Div(
                    style={"margin-top": "20px"},
                    children=[
                        html.Div(
                            style={"display": "flex", "justify-content": "space-between"},
                            children=[
                                html.Label("Name", style={"font-size": "20px", "text-shadow": "2px 2px 5px rgba(0, 0, 0, 0.2)"}),
                                html.P("Your Name", style={"margin-bottom": "15px", "margin-left": "10px", "font-size": "20px", "text-shadow": "2px 2px 5px rgba(0, 0, 0, 0.2)"})
                            ]
                        ),
                        html.Hr(style={"border": "none", "border-top": "1px solid #ddd", "box-shadow": "0 2px 4px rgba(0, 0, 0, 0.1)", "margin": "5px 0"}),

                        # Email
                        html.Div(
                            style={"display": "flex", "justify-content": "space-between"},
                            children=[
                                html.Label("Email account", style={"font-size": "20px", "text-shadow": "2px 2px 5px rgba(0, 0, 0, 0.2)"}),
                                html.P("yourname@gmail.com", style={"margin-bottom": "15px", "font-size": "20px", "text-shadow": "2px 2px 5px rgba(0, 0, 0, 0.2)"})
                            ]
                        ),
                        html.Hr(style={"border": "none", "border-top": "1px solid #ddd", "box-shadow": "0 2px 4px rgba(0, 0, 0, 0.1)", "margin": "5px 0"}),

                        # Telefone
                        html.Div(
                            style={"display": "flex", "justify-content": "space-between"},
                            children=[
                                html.Label("Mobile number", style={"font-size": "20px", "text-shadow": "2px 2px 5px rgba(0, 0, 0, 0.2)"}),
                                html.P("Add number", style={"margin-bottom": "15px", "font-size": "20px", "text-shadow": "2px 2px 5px rgba(0, 0, 0, 0.2)"})
                            ]
                        ),
                        html.Hr(style={"border": "none", "border-top": "1px solid #ddd", "box-shadow": "0 2px 4px rgba(0, 0, 0, 0.1)", "margin": "5px 0"}),

                        # Localização
                        html.Div(
                            style={"display": "flex", "justify-content": "space-between"},
                            children=[
                                html.Label("Location", style={"font-size": "20px", "text-shadow": "2px 2px 5px rgba(0, 0, 0, 0.2)"}),
                                html.P("USA", style={"margin-bottom": "15px", "font-size": "20px", "text-shadow": "2px 2px 5px rgba(0, 0, 0, 0.2)"})
                            ]
                        ),
                        html.Hr(style={"border": "none", "border-top": "1px solid #ddd", "box-shadow": "0 2px 4px rgba(0, 0, 0, 0.1)", "margin": "5px 0"}),

                        # Password
                        html.Div(
                            style={"display": "flex", "justify-content": "space-between"},
                            children=[
                                html.Label("Password", style={"font-size": "20px", "text-shadow": "2px 2px 5px rgba(0, 0, 0, 0.2)"}),
                                html.P("*********", style={"margin-bottom": "15px", "font-size": "20px", "text-shadow": "2px 2px 5px rgba(0, 0, 0, 0.2)"})
                            ]
                        ),
                    ]
                ),
                
                # Botão de "Save Changes"
                html.Div(
                    style={"display": "flex", "justify-content": "center", "margin-top": "30px"},
                    children=[
                        html.Button(
                            "Save Changes",
                            style={
                                "background-color": "#2489FF",
                                "color": "white",
                                "padding": "10px 30px",
                                "border": "none",
                                "border-radius": "6px",
                                "cursor": "pointer",
                                "font-size": "18px",
                            }
                        ),
                    ]
                ),
            ]
        )
    ]
)

# Layout principal
app.layout = html.Div(
    style={"display": "flex"},
    children=[
        dcc.Store(id="sidebar-width", data="80px"),
        vertical_header,
        profile_page_content,
    ],
)

# Callback para mudar a largura do cabeçalho vertical (não implementado no exemplo, mas pode ser adicionado)
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

# Rodar o app
if __name__ == "__main__":
    app.run_server(debug=True)
