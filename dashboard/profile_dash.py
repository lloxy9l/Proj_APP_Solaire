import dash
from dash import html
from navbar import vertical_header  # Importando a navbar separada

app = dash.Dash(__name__)

# Conteúdo da página de perfil
profile_page_content = html.Div(
    style={
        "margin-left": "80px",  # Ajustando para a largura da barra lateral
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
                html.Div(
                    style={"margin-top": "10px"},
                    children=[
                        html.Div(
                            style={"display": "flex", "align-items": "center"},
                            children=[
                                html.Div(
                                    style={
                                        "position": "relative",
                                        "width": "120px",
                                        "height": "120px",
                                        "border-radius": "50%",
                                        "background-image": "url('./assets/img/user_image.jpeg')",
                                        "background-size": "cover",
                                        "background-position": "center",
                                        "border": "3px solid white",
                                    },
                                    children=[
                                        html.Div(
                                            style={
                                                "position": "absolute",
                                                "bottom": "5px",
                                                "right": "5px",
                                                "background-color": "#005dff",
                                                "border-radius": "50%",
                                                "padding": "5px",
                                                "background-image": "url('./assets/svg/edit.svg')",
                                                "background-size": "contain",
                                                "background-repeat": "no-repeat",
                                                "width": "30px", 
                                                "height": "30px", 
                                            },
                                            children=[
                                                html.Img(
                                                    src="assets/img/edit-icon.png",
                                                    style={"width": "20px", "height": "20px"},
                                                ),
                                            ],
                                        ),
                                    ],
                                ),
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

                # Detalhes do usuário - Mantido como antes
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
                                html.P("Your location", style={"margin-bottom": "15px", "font-size": "20px", "text-shadow": "2px 2px 5px rgba(0, 0, 0, 0.2)"})
                            ]
                        ),
                        html.Hr(style={"border": "none", "border-top": "1px solid #ddd", "box-shadow": "0 2px 4px rgba(0, 0, 0, 0.1)", "margin": "5px 0"}),
                        # Senha
                        html.Div(
                            style={"display": "flex", "justify-content": "space-between"},
                            children=[
                                html.Label("Password", style={"font-size": "20px", "text-shadow": "2px 2px 5px rgba(0, 0, 0, 0.2)"}),
                                html.P("********", style={"margin-bottom": "15px", "font-size": "20px", "text-shadow": "2px 2px 5px rgba(0, 0, 0, 0.2)"})
                            ]
                        ),
                    ]
                ),

                # Botões para editar e salvar
                html.Div(
                    style={"margin-top": "30px", "display": "flex", "justify-content": "space-between"},
                    children=[
                        html.Button(
                            "Modifier",  # Botão para Editar em francês
                            style={"background-color": "#005dff", "color": "white", "padding": "10px 20px", "border": "none", "border-radius": "5px", "cursor": "pointer"}
                        ),
                        html.Button(
                            "Sauvegarder",  # Botão para Salvar em francês
                            style={"background-color": "#28a745", "color": "white", "padding": "10px 20px", "border": "none", "border-radius": "5px", "cursor": "pointer"}
                        ),
                    ]
                ),
            ]
        )
    ]
)

app.layout = html.Div(
    style={"display": "flex"},
    children=[
        vertical_header,  # Incluindo a navbar
        profile_page_content,  # O conteúdo da página de perfil
    ],
)

if __name__ == "__main__":
    app.run_server(debug=True)
