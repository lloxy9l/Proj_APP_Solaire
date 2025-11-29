import base64
import dash
from dash import html, dcc, Input, Output, State, no_update

from services.chat_service import generate_chat_response


def get_chatbot_layout():
    """
    Composants globaux du chatbot :
    - Bulle flottante en bas à droite
    - Fenêtre de discussion (hidden au début)
    - Stores pour l'historique, l'image et l'action carte
    À inclure UNE FOIS dans app.layout pour être présent sur toutes les pages.
    """
    return html.Div(
        [
            # 🔵 Bulle flottante
            html.Button(
                id="chatbot-toggle-btn",
                children=html.Span("💬", style={"font-size": "26px"}),
                style={
                    "position": "fixed",
                    "bottom": "24px",
                    "right": "24px",
                    "width": "64px",
                    "height": "64px",
                    "border-radius": "50%",
                    "border": "none",
                    "background": "linear-gradient(135deg, #005DFF, #2C82FF)",
                    "color": "white",
                    "box-shadow": "0 8px 20px rgba(0, 0, 0, 0.25)",
                    "cursor": "pointer",
                    "zIndex": 9999,
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "center",
                },
                n_clicks=0,
            ),

            # 🪟 Fenêtre du chatbot (popup)
            html.Div(
                id="chatbot-window",
                style={
                    "position": "fixed",
                    "bottom": "100px",
                    "right": "24px",
                    "width": "520px",      # plus large
                    "height": "80vh",      # hauteur relative à l'écran
                    "maxHeight": "820px",  # limite max
                    "backgroundColor": "#ffffff",
                    "border-radius": "18px",
                    "box-shadow": "0 16px 40px rgba(0, 0, 0, 0.30)",
                    "display": "none",     # caché par défaut
                    "flexDirection": "column",
                    "overflow": "hidden",
                    "zIndex": 9998,
                },
                children=[
                    # 🧢 Header de la fenêtre
                    html.Div(
                        style={
                            "background": "linear-gradient(135deg, #005DFF, #2F9BFF)",
                            "padding": "14px 16px",
                            "display": "flex",
                            "alignItems": "center",
                            "justifyContent": "space-between",
                            "color": "white",
                        },
                        children=[
                            html.Div(
                                style={"display": "flex", "alignItems": "center", "gap": "10px"},
                                children=[
                                    html.Div(
                                        "☀️",
                                        style={
                                            "width": "32px",
                                            "height": "32px",
                                            "border-radius": "50%",
                                            "background": "rgba(255, 255, 255, 0.15)",
                                            "display": "flex",
                                            "alignItems": "center",
                                            "justifyContent": "center",
                                            "font-size": "18px",
                                        },
                                    ),
                                    html.Div(
                                        children=[
                                            html.Div(
                                                "SolarXBot",
                                                style={
                                                    "font-weight": "600",
                                                    "font-size": "16px",
                                                },
                                            ),
                                            html.Div(
                                                "Assistant IA pour vos données solaires à Genève",
                                                style={
                                                    "font-size": "11px",
                                                    "opacity": 0.9,
                                                },
                                            ),
                                        ]
                                    ),
                                ],
                            ),
                            html.Button(
                                "✕",
                                id="chatbot-close-btn",
                                n_clicks=0,
                                style={
                                    "border": "none",
                                    "background": "transparent",
                                    "color": "white",
                                    "font-size": "18px",
                                    "cursor": "pointer",
                                },
                            ),
                        ],
                    ),

                    # 📨 Zone des messages (scrollable) + bulle de "typing"
                    html.Div(
                        style={
                            "flex": "1",
                            "display": "flex",
                            "flexDirection": "column",
                            "background": "#f5f7fb",
                            "minHeight": 0,  # IMPORTANT pour le scroll dans un flex
                        },
                        children=[
                            # Historique scrollable (flex:1)
                            html.Div(
                                id="chat-history",
                                style={
                                    "padding": "12px 14px",
                                    "overflowY": "auto",
                                    "flex": "1",
                                    "minHeight": 0,  # IMPORTANT pour autoriser le scroll
                                },
                                children=[
                                    html.Div(
                                        className="chat-message bot",
                                        style={
                                            "display": "flex",
                                            "margin-bottom": "8px",
                                        },
                                        children=[
                                            html.Div(
                                                "🤖",
                                                style={
                                                    "width": "28px",
                                                    "height": "28px",
                                                    "border-radius": "50%",
                                                    "backgroundColor": "#005DFF",
                                                    "color": "white",
                                                    "display": "flex",
                                                    "alignItems": "center",
                                                    "justifyContent": "center",
                                                    "font-size": "16px",
                                                    "margin-right": "8px",
                                                    "flex-shrink": 0,
                                                },
                                            ),
                                            html.Div(
                                                style={
                                                    "backgroundColor": "white",
                                                    "border-radius": "14px",
                                                    "padding": "8px 12px",
                                                    "box-shadow": "0 2px 6px rgba(0,0,0,0.06)",
                                                    "font-size": "13px",
                                                },
                                                children=(
                                                    "Bonjour 👋 Je suis SolarXBot. Pose-moi des questions sur les communes, "
                                                    "l’ensoleillement, la consommation d’électricité ou le potentiel des panneaux "
                                                    "solaires à Genève."
                                                ),
                                            ),
                                        ],
                                    )
                                ],
                            ),
                            # Bulle "SolarXBot est en train d'écrire..." avec 3 points animés
                            html.Div(
                                id="typing-container",
                                style={
                                    "minHeight": "28px",
                                    "padding": "0 14px 6px 14px",
                                },
                                children=dcc.Loading(
                                    id="chat-typing-loader",
                                    type="dots",      # animation 3 points
                                    fullscreen=False,
                                    children=html.Div(
                                        id="typing-placeholder",
                                        style={},
                                    ),
                                ),
                            ),
                        ],
                    ),

                    # ⌨️ Barre d'entrée + upload + prévisualisation image
                    html.Div(
                        style={
                            "border-top": "1px solid #e0e3ec",
                            "padding": "8px 10px",
                            "backgroundColor": "#ffffff",
                        },
                        children=[
                            dcc.Upload(
                                id="chat-image-upload",
                                children=html.Div("📷 Ajouter une image (optionnel)"),
                                style={
                                    "border": "1px dashed #b3c4ff",
                                    "border-radius": "10px",
                                    "padding": "4px 8px",
                                    "cursor": "pointer",
                                    "background-color": "#f3f6ff",
                                    "font-size": "11px",
                                    "margin-bottom": "4px",
                                },
                                multiple=False,
                            ),
                            # 🖼️ Prévisualisation de l'image dans la zone d'input
                            html.Div(
                                id="chat-image-preview",
                                style={
                                    "marginBottom": "6px",
                                },
                            ),
                            html.Div(
                                style={
                                    "display": "flex",
                                    "gap": "6px",
                                    "alignItems": "flex-end",
                                },
                                children=[
                                    # dcc.Input pour pouvoir utiliser Enter (n_submit)
                                    dcc.Input(
                                        id="chat-input",
                                        type="text",
                                        placeholder="Pose ta question sur le solaire, la météo ou la consommation...",
                                        style={
                                            "flex": 1,
                                            "height": "40px",
                                            "border-radius": "10px",
                                            "border": "1px solid #d0d4e6",
                                            "padding": "6px 8px",
                                            "font-size": "13px",
                                            "outline": "none",
                                            "background-color": "#fdfdff",
                                        },
                                    ),
                                    html.Button(
                                        "Envoyer",
                                        id="chat-send-btn",
                                        n_clicks=0,
                                        style={
                                            "background": "linear-gradient(135deg, #005DFF, #2F9BFF)",
                                            "color": "white",
                                            "border": "none",
                                            "border-radius": "10px",
                                            "padding": "10px 14px",
                                            "cursor": "pointer",
                                            "font-size": "13px",
                                            "font-weight": "600",
                                            "flex-shrink": 0,
                                        },
                                    ),
                                ],
                            ),
                            html.Div(
                                id="chat-error",
                                style={"color": "#e74c3c", "font-size": "11px", "margin-top": "4px"},
                            ),
                        ],
                    ),

                    # 🧠 Stores internes
                    dcc.Store(id="chat-store", data=[]),
                    dcc.Store(id="chat-image-bytes"),
                    dcc.Store(id="chat-map-action"),
                ],
            ),
        ]
    )


def register_chatbot_callbacks(app: dash.Dash):
    """
    Enregistre :
    - le callback d'ouverture/fermeture de la fenêtre
    - le callback unique qui gère :
        * la prévisualisation image
        * l'envoi de message (Gemini + SQL + zone)
    """

    # 1️⃣ Toggle ouverture / fermeture de la fenêtre
    @app.callback(
        Output("chatbot-window", "style"),
        Input("chatbot-toggle-btn", "n_clicks"),
        Input("chatbot-close-btn", "n_clicks"),
        State("chatbot-window", "style"),
        prevent_initial_call=True,
    )
    def toggle_chat_window(n_open, n_close, style):
        style = style or {}
        ctx = dash.callback_context
        trigger = ctx.triggered[0]["prop_id"].split(".")[0]

        # Style de base de la fenêtre
        base_style = {
            "position": "fixed",
            "bottom": "100px",
            "right": "24px",
            "width": "520px",
            "height": "80vh",
            "maxHeight": "820px",
            "backgroundColor": "#ffffff",
            "border-radius": "18px",
            "box-shadow": "0 16px 40px rgba(0, 0, 0, 0.30)",
            "flexDirection": "column",
            "overflow": "hidden",
            "zIndex": 9998,
        }

        # Fermeture explicite
        if trigger == "chatbot-close-btn":
            base_style["display"] = "none"
            return base_style

        # Ouverture / fermeture via la bulle
        current_display = style.get("display", "none")
        if current_display == "none":
            base_style["display"] = "flex"
        else:
            base_style["display"] = "none"

        return base_style

    # 2️⃣ Callback unique :
    #   - upload image → mettre à jour prévisualisation SANS envoyer de message
    #   - Enter ou bouton Envoyer → envoyer message + image si présente
    @app.callback(
        [
            Output("chat-history", "children"),
            Output("chat-store", "data"),
            Output("chat-error", "children"),
            Output("chat-image-bytes", "data"),
            Output("typing-placeholder", "children"),
            Output("chat-input", "value"),
            Output("chat-image-preview", "children"),
            Output("chat-map-action", "data"),
        ],
        [
            Input("chat-send-btn", "n_clicks"),
            Input("chat-input", "n_submit"),          # Enter dans le champ input
            Input("chat-image-upload", "contents"),   # upload image → prévisualisation
        ],
        [
            State("chat-input", "value"),
            State("chat-store", "data"),
            State("chat-history", "children"),
            State("chat-image-bytes", "data"),
        ],
        prevent_initial_call=True,
    )
    def handle_chat(
        n_clicks,
        n_submit,
        image_contents,
        user_text,
        history,
        current_messages,
        image_bytes_b64,
    ):
        ctx = dash.callback_context
        if not ctx.triggered:
            return (
                no_update,
                no_update,
                no_update,
                no_update,
                "",
                no_update,
                no_update,
                no_update,
            )

        trigger = ctx.triggered[0]["prop_id"].split(".")[0]

        # 🖼️ CAS 1 : l'utilisateur vient d'uploader une image → prévisualiser uniquement
        if trigger == "chat-image-upload":
            if not image_contents:
                # effacer la preview si rien
                return (
                    no_update,   # chat-history
                    no_update,   # chat-store
                    "",          # pas d'erreur
                    image_bytes_b64,   # on garde la dernière image bytes
                    "",          # typing-placeholder
                    user_text,   # on garde le texte éventuel
                    "",          # preview vidée
                    no_update,   # chat-map-action
                )
            # mettre à jour la prévisualisation
            preview = html.Img(
                src=image_contents,
                style={
                    "maxWidth": "120px",
                    "maxHeight": "100px",
                    "borderRadius": "10px",
                    "boxShadow": "0 2px 6px rgba(0,0,0,0.15)",
                },
            )
            # on stocke aussi les bytes pour le backend (si besoin plus tard)
            try:
                content_type, content_string = image_contents.split(",")
                _ = content_type
                new_image_bytes_b64 = content_string
            except Exception:
                new_image_bytes_b64 = None

            return (
                no_update,
                no_update,
                "",
                new_image_bytes_b64 if new_image_bytes_b64 else image_bytes_b64,
                "",
                user_text,
                preview,
                no_update,
            )

        # 📨 CAS 2 : envoi de message (bouton ou Enter)
        # Si pas de texte → message d'erreur
        if not user_text or str(user_text).strip() == "":
            return (
                no_update,
                no_update,
                "Merci d'écrire une question.",
                image_bytes_b64,
                "",
                user_text,  # on laisse ce qu'il y a dans le champ
                no_update,
                no_update,
            )

        history = history or []
        current_messages = current_messages or []

        # 🔍 Décodage image pour Gemini (backend)
        image_bytes = None
        mime_type = "image/jpeg"
        if image_contents:
            try:
                content_type, content_string = image_contents.split(",")
                if ";" in content_type:
                    mime_type = content_type.split(":")[1].split(";")[0]
                image_bytes = base64.b64decode(content_string)
            except Exception:
                image_bytes = None
        elif image_bytes_b64:
            try:
                image_bytes = base64.b64decode(image_bytes_b64)
            except Exception:
                image_bytes = None

        # Ajout question utilisateur à l'historique "logique"
        history.append({"role": "user", "text": user_text})

        # 💬 Contenu de la bulle utilisateur (texte + éventuelle image envoyée)
        user_bubble_inner = []

        # Texte
        user_bubble_inner.append(
            html.Div(
                user_text,
                style={
                    "margin-bottom": "4px",
                    "whiteSpace": "pre-wrap",
                },
            )
        )

        # Miniature de l'image DANS la bulle (une fois envoyée)
        if image_contents:
            user_bubble_inner.append(
                html.Img(
                    src=image_contents,
                    style={
                        "maxWidth": "140px",
                        "maxHeight": "120px",
                        "borderRadius": "10px",
                        "marginTop": "4px",
                        "marginBottom": "2px",
                        "boxShadow": "0 2px 6px rgba(0,0,0,0.15)",
                    },
                )
            )

        # Bulle UI utilisateur
        current_messages.append(
            html.Div(
                className="chat-message user",
                style={
                    "display": "flex",
                    "justifyContent": "flex-end",
                    "margin-bottom": "8px",
                },
                children=[
                    html.Div(
                        style={
                            "maxWidth": "80%",
                            "background": "linear-gradient(135deg, #005DFF, #2F9BFF)",
                            "color": "white",
                            "border-radius": "14px",
                            "padding": "8px 12px",
                            "font-size": "13px",
                            "box-shadow": "0 2px 6px rgba(0,0,0,0.12)",
                        },
                        children=user_bubble_inner,
                    )
                ],
            )
        )

        # 🔁 Appel à Gemini + SQL via ton service backend
        try:
            bot_answer, zone_info = generate_chat_response(
                history=history,
                user_message=user_text,
                image_bytes=image_bytes,
                mime_type=mime_type,
            )
        except Exception as e:
            # On garde l'historique, on vide l'image, on vide la preview, on vide le champ
            return (
                current_messages,
                history,
                f"Erreur lors de l'appel à Gemini : {e}",
                None,
                "",
                "",
                "",
                no_update,
            )

        # Ajout réponse bot dans l'historique logique
        history.append({"role": "model", "text": bot_answer})

        # 🧭 Optionnel : petite carte/bouton au-dessus de la réponse si zone détectée
        bot_children = []
        map_action_payload = None

        if zone_info and isinstance(zone_info, dict) and zone_info.get("name"):
            zone_label = zone_info.get("name")
            # On prépare la donnée pour la carte (commune ou point)
            map_action_payload = {
                "type": zone_info.get("type"),
                "name": zone_info.get("name"),
                "idpoint": zone_info.get("idpoint"),
            }

            # Petite "card" cliquable qui renvoie vers la page de carte
            bot_children.append(
                html.Div(
                    style={
                        "margin-bottom": "6px",
                    },
                    children=html.A(
                        f"📍 Voir la carte pour {zone_label}",
                        href="/electricite",   # à adapter si ta page carte a un autre pathname
                        style={
                            "display": "inline-block",
                            "padding": "6px 10px",
                            "borderRadius": "12px",
                            "background": "#EAF3FF",
                            "color": "#005DFF",
                            "fontSize": "12px",
                            "fontWeight": "600",
                            "textDecoration": "none",
                        },
                    ),
                )
            )

        # Puis le texte de la réponse
        bot_children.append(
            html.Div(
                bot_answer,
                style={
                    "whiteSpace": "pre-wrap",
                },
            )
        )

        # Bulle UI bot
        current_messages.append(
            html.Div(
                className="chat-message bot",
                style={
                    "display": "flex",
                    "alignItems": "flex-start",
                    "margin-bottom": "8px",
                },
                children=[
                    html.Div(
                        "🤖",
                        style={
                            "width": "28px",
                            "height": "28px",
                            "border-radius": "50%",
                            "backgroundColor": "#005DFF",
                            "color": "white",
                            "display": "flex",
                            "alignItems": "center",
                            "justifyContent": "center",
                            "font-size": "16px",
                            "margin-right": "8px",
                            "flex-shrink": 0,
                        },
                    ),
                    html.Div(
                        style={
                            "maxWidth": "80%",
                            "backgroundColor": "white",
                            "border-radius": "14px",
                            "padding": "8px 12px",
                            "font-size": "13px",
                            "box-shadow": "0 2px 6px rgba(0,0,0,0.06)",
                        },
                        children=bot_children,
                    ),
                ],
            )
        )

        # 🔚 Après envoi :
        # - on nettoie l'image backend (image-bytes)
        # - on vide le champ de texte
        # - on efface la prévisualisation
        return (
            current_messages,
            history,
            "",
            None,   # reset image_bytes
            "",
            "",     # vider l'input
            "",     # enlever la preview
            map_action_payload,  # info pour la carte (ou None)
        )
