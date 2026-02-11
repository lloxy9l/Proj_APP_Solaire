from __future__ import annotations
import base64
import json
import uuid
import dash
from dash import html, dcc, Input, Output, State, no_update
from dash.dependencies import ALL
import dash_bootstrap_components as dbc

from services.chat_service import generate_chat_response
try:
    from services.memory_service import get_memory_service
except Exception:  # pragma: no cover
    get_memory_service = None

def _bot_avatar():
    return html.Div(
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
    )


def _user_avatar():
    return html.Div(
        "🧑‍💻",
        style={
            "width": "28px",
            "height": "28px",
            "border-radius": "50%",
            "backgroundColor": "#2F9BFF",
            "color": "white",
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "center",
            "font-size": "16px",
            "margin-right": "8px",
            "flex-shrink": 0,
        },
    )


def _greeting_bubble():
    return html.Div(
        className="chat-message bot",
        style={"display": "flex", "margin-bottom": "8px"},
        children=[
            _bot_avatar(),
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


def _user_bubble(text: str):
    return html.Div(
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
                children=html.Div(text or "", style={"whiteSpace": "pre-wrap"}),
            )
        ],
    )

# redirection vers la carte dyal dak sujet fhal temp, precipi, ... avec les coords si dispo
def _zone_card(zone_info: dict):
    """Petit lien cliquable 'voir la carte' vers la page correcte + coords."""
    if not zone_info or not isinstance(zone_info, dict) or not zone_info.get("name"):
        return None

    zone_label = zone_info.get("name")
    page = (zone_info.get("page") or "").strip().lower()
    # Routes Dash
    route_map = {
        "electricite": "/electricite",
        "consommation": "/electricite",
        "optimisation": "/optimisation",
        "production": "/production",
        "ensoleillement": "/ensoleillement",
        "temperature": "/temperature",
        "precipitation": "/precipitation",
        "zones-industrielles": "/zones-industrielles",
    }
    href = route_map.get(page, "/optimisation")

    # Ajouter coords dans l'URL si dispo
    if zone_info.get("lat") is not None and zone_info.get("lon") is not None:
        try:
            lat = float(zone_info.get("lat"))
            lon = float(zone_info.get("lon"))
            zoom = int(zone_info.get("zoom") or 14)
            from urllib.parse import urlencode
            href = f"{href}?" + urlencode({
                "lat": f"{lat:.6f}",
                "lon": f"{lon:.6f}",
                "zoom": str(zoom),
                "name": str(zone_label),
            })
        except Exception:
            pass

    return html.Div(
        style={"margin-bottom": "6px"},
        children=html.A(
            f"📍 Voir la carte pour {zone_label}",
            href=href,
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


def _bot_bubble(text: str, zone_info=None, suggestions: Optional[list[dict]] = None):
    bot_children = []
    z = _zone_card(zone_info)
    if z is not None:
        bot_children.append(z)

    bot_children.append(html.Div(text or "", style={"whiteSpace": "pre-wrap"}))

    # Si lat/lon disponibles → afficher dans la bulle (utile)
    if zone_info and isinstance(zone_info, dict) and zone_info.get("lat") is not None and zone_info.get("lon") is not None:
        bot_children.append(
            html.Div(
                f"🧭 Coordonnées: lat={zone_info.get('lat')}, lon={zone_info.get('lon')}",
                style={"marginTop": "6px", "fontSize": "11px", "opacity": 0.75},
            )
        )

    # Suggestions dynamiques (boutons cliquables)
    if suggestions and isinstance(suggestions, list):
        btns = []
        for i, s in enumerate(suggestions[:5]):
            if not isinstance(s, dict):
                continue
            label = str(s.get('label') or '').strip()
            query = str(s.get('query') or label).strip()
            if not label or not query:
                continue
            btns.append(
                html.Button(
                    label,
                    id={"type": "chat-suggestion-btn", "index": query},
                    n_clicks=0,
                    style={
                        "border": "1px solid #dbe6ff",
                        "background": "#f3f7ff",
                        "color": "#005DFF",
                        "borderRadius": "999px",
                        "padding": "6px 10px",
                        "fontSize": "12px",
                        "cursor": "pointer",
                        "marginRight": "6px",
                        "marginTop": "6px",
                    },
                )
            )
        if btns:
            bot_children.append(
                html.Div(
                    btns,
                    style={"display": "flex", "flexWrap": "wrap", "gap": "6px", "marginTop": "6px"},
                )
            )

    return html.Div(
        className="chat-message bot",
        style={
            "display": "flex",
            "alignItems": "flex-start",
            "margin-bottom": "8px",
        },
        children=[
            _bot_avatar(),
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


def _render_history(messages: list[dict]) -> list:
    """messages: [{'role':'user'|'model', 'text':...}, ...]"""
    children = [_greeting_bubble()]
    for m in messages or []:
        role = m.get("role")
        text = m.get("text", "")
        meta = m.get("metadata") or {}
        zone = meta.get("zone_info") if isinstance(meta, dict) else None
        sugg = meta.get("suggestions") if isinstance(meta, dict) else None
        if role == "user":
            children.append(_user_bubble(text))
        else:
            children.append(_bot_bubble(text, zone_info=zone if isinstance(zone, dict) else None, suggestions=sugg if isinstance(sugg, list) else None))
    return children


def _safe_decode_upload(contents: str | None):
    if not contents:
        return None, None, None
    try:
        header, b64data = contents.split(",", 1)
        mime = header.split(";")[0].split(":")[1]
        raw = base64.b64decode(b64data)
        return raw, mime, contents
    except Exception:
        return None, None, None


def get_chatbot_layout():
    """
    Composants globaux du chatbot :
    - Bulle flottante en bas à droite
    - Fenêtre de discussion (hidden au début)
    - Stores : historique, image, action carte, sessions
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
                    "width": "520px",
                    "height": "80vh",
                    "maxHeight": "820px",
                    "backgroundColor": "#ffffff",
                    "border-radius": "18px",
                    "box-shadow": "0 16px 40px rgba(0, 0, 0, 0.30)",
                    "display": "none",
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
                                                style={"font-weight": "600", "font-size": "16px"},
                                            ),
                                            html.Div(
                                                "Assistant IA pour vos données solaires à Genève",
                                                style={"font-size": "11px", "opacity": 0.9},
                                            ),
                                        ]
                                    ),
                                ],
                            ),

                            # Actions header (menu + close)
                            html.Div(
                                style={"display": "flex", "gap": "10px", "alignItems": "center"},
                                children=[
                                    html.Button(
                                        "☰",
                                        id="chatbot-menu-btn",
                                        n_clicks=0,
                                        style={
                                            "border": "none",
                                            "background": "rgba(255,255,255,0.12)",
                                            "color": "white",
                                            "font-size": "16px",
                                            "cursor": "pointer",
                                            "borderRadius": "10px",
                                            "padding": "6px 10px",
                                        },
                                        title="Historique",
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
                                        title="Fermer",
                                    ),
                                ],
                            ),
                        ],
                    ),

                    # 🧾 Sidebar historique (overlay)
                    html.Div(
                        id="chatbot-sidebar",
                        style={
                            "position": "absolute",
                            "top": 0,
                            "left": 0,
                            "height": "100%",
                            "width": "260px",
                            "background": "#ffffff",
                            "borderRight": "1px solid #e0e3ec",
                            "boxShadow": "6px 0 18px rgba(0,0,0,0.12)",
                            "transform": "translateX(-110%)",
                            "transition": "transform 160ms ease",
                            "zIndex": 10000,
                            "display": "flex",
                            "flexDirection": "column",
                        },
                        children=[
                            html.Div(
                                style={
                                    "padding": "10px 10px",
                                    "borderBottom": "1px solid #eef1f7",
                                    "background": "#f7f9ff",
                                },
                                children=[
                                    html.Div(
                                        "Conversations",
                                        style={"fontWeight": "700", "fontSize": "13px", "marginBottom": "6px"},
                                    ),
                                    html.Button(
                                        "➕ Nouveau chat",
                                        id="chat-new-chat-btn",
                                        n_clicks=0,
                                        style={
                                            "width": "100%",
                                            "border": "none",
                                            "borderRadius": "10px",
                                            "padding": "8px 10px",
                                            "background": "linear-gradient(135deg, #005DFF, #2F9BFF)",
                                            "color": "white",
                                            "fontWeight": "700",
                                            "cursor": "pointer",
                                            "fontSize": "12px",
                                        },
                                    ),
                                ],
                            ),
                            html.Div(
                                id="chat-sessions-list",
                                style={"padding": "10px", "overflowY": "auto", "flex": "1"},
                            ),
                            html.Div(
                                style={"padding": "10px", "borderTop": "1px solid #eef1f7", "fontSize": "11px", "opacity": 0.75},
                                children="Astuce: clique sur une conversation pour la recharger.",
                            ),
                        ],
                    ),

                    # 📨 Zone des messages + loader
                    html.Div(
                        style={
                            "flex": "1",
                            "display": "flex",
                            "flexDirection": "column",
                            "background": "#f5f7fb",
                            "minHeight": 0,
                            "position": "relative",
                        },
                        children=[
                            html.Div(
                                id="chat-history",
                                style={"padding": "12px 14px", "overflowY": "auto", "flex": "1", "minHeight": 0},
                                children=[_greeting_bubble()],
                            ),
                            html.Div(
                                id="typing-container",
                                style={"minHeight": "28px", "padding": "0 14px 6px 14px"},
                                children=dcc.Loading(
                                    id="chat-typing-loader",
                                    type="dots",
                                    fullscreen=False,
                                    children=html.Div(id="typing-placeholder", style={}),
                                ),
                            ),
                        ],
                    ),

                    
# ⌨️ Barre d'entrée + upload + preview
                    html.Div(
                        style={"border-top": "1px solid #e0e3ec", "padding": "8px 10px", "backgroundColor": "#ffffff"},
                        children=[
                            dcc.Upload(
                                id="chat-image-upload",
                                children=html.Div(
                                    "🖼️",
                                    title="Ajouter une image",
                                    style={
                                        "font-size": "18px",
                                        "cursor": "pointer",
                                        "user-select": "none",
                                    },
                                ),
                                style={
                                    "width": "40px",
                                    "height": "40px",
                                    "display": "flex",
                                    "align-items": "center",
                                    "justify-content": "center",
                                    "border": "1px solid #d0d4e6",
                                    "border-radius": "10px",
                                    "background-color": "#f3f6ff",
                                },
                                multiple=False,
                            ),
                            html.Div(id="chat-image-preview", style={"marginBottom": "6px"}),
                            html.Div(
                                style={"display": "flex", "gap": "6px", "alignItems": "flex-end"},
                                children=[
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
                            html.Div(id="chat-error", style={"color": "#e74c3c", "font-size": "11px", "margin-top": "4px"}),
                        ],
                    ),

                    # Stores
                    dcc.Store(id="chat-store", data=[]),
                    dcc.Store(id="chat-image-bytes"),
                    dcc.Store(id="chat-map-action"),
                    dcc.Store(id="chat-session-id"),
                    dcc.Store(id="chat-sessions", data=[]),
                    dcc.Store(id="chat-sidebar-open", data=False),
                ],
            ),
            # =========================
            # MODAL : Carte & Indicateurs
            # =========================
            dbc.Modal(
                [
                    dbc.ModalHeader(
                        [
                            dbc.ModalTitle("Carte & Indicateurs"),
                            html.Button(
                                "✕",
                                id="map-modal-close",
                                n_clicks=0,
                                style={
                                    "marginLeft": "auto",
                                    "border": "none",
                                    "background": "transparent",
                                    "fontSize": "18px",
                                    "cursor": "pointer",
                                },
                            ),
                        ],
                        style={"display": "flex", "alignItems": "center"},
                    ),
                    dbc.ModalBody(
                        html.Iframe(
                            id="map-modal-iframe",
                            src="",
                            style={
                                "width": "100%",
                                "height": "80vh",
                                "border": "0",
                                "borderRadius": "12px",
                            },
                        ),
                        style={"padding": "0"},
                    ),
                ],
                id="map-modal",
                is_open=False,
                size="xl",
                centered=True,
                backdrop=True,
                scrollable=False,
            ),

        ]
    )


def register_chatbot_callbacks(app: dash.Dash):
    # 1) Toggle ouverture/fermeture fenêtre
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

        if trigger == "chatbot-close-btn":
            base_style["display"] = "none"
            return base_style

        current_display = style.get("display", "none")
        base_style["display"] = "flex" if current_display == "none" else "none"
        return base_style

    # 2) Sidebar toggle
    @app.callback(
        [Output("chatbot-sidebar", "style"), Output("chat-sidebar-open", "data")],
        Input("chatbot-menu-btn", "n_clicks"),
        State("chat-sidebar-open", "data"),
        State("chatbot-sidebar", "style"),
        prevent_initial_call=True,
    )
    def toggle_sidebar(n, is_open, current_style):
        is_open = bool(is_open)
        new_open = not is_open
        style = dict(current_style or {})
        style["transform"] = "translateX(0%)" if new_open else "translateX(-110%)"
        return style, new_open

    # 3) Callback unique: upload, send, new chat, switch session
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
            Output("chat-session-id", "data"),
            Output("chat-sessions", "data"),
            Output("chat-sessions-list", "children"),
        ],
        [
            Input("chat-send-btn", "n_clicks"),
            Input("chat-input", "n_submit"),
            Input("chat-image-upload", "contents"),
            Input("chat-new-chat-btn", "n_clicks"),
            Input({"type": "chat-session-btn", "index": ALL}, "n_clicks"),
            Input({"type": "chat-suggestion-btn", "index": ALL}, "n_clicks"),
        ],
        [
            State("chat-input", "value"),
            State("chat-store", "data"),
            State("chat-history", "children"),
            State("chat-image-bytes", "data"),
            State("chat-session-id", "data"),
            State("chat-sessions", "data"),
        ],
        prevent_initial_call=True,
    )
    def main_chat_callback(
        n_send,
        n_submit,
        upload_contents,
        n_new_chat,
        session_btn_clicks,
        suggestion_btn_clicks,
        user_text,
        history,
        current_messages,
        image_bytes_store,
        session_id,
        sessions_store,
    ):
        ctx = dash.callback_context
        trigger = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else ""

        history = history or []
        current_messages = current_messages or [_greeting_bubble()]
        sessions_store = sessions_store or []

        mem = get_memory_service() if get_memory_service is not None else None

        # Helper: refresh sessions
        def _refresh_sessions():
            if not mem:
                return sessions_store
            try:
                return mem.get_all_sessions(limit=30)
            except Exception:
                return sessions_store

        # Helper: render sessions list UI
        def _render_sessions_list(sessions, active_id):
            items = []
            for s in sessions or []:
                sid = s.get("session_id")
                title = s.get("title") or "Conversation"
                cnt = int(s.get("message_count") or 0)
                is_active = (sid == active_id)
                items.append(
                    html.Button(
                        [
                            html.Div(title, style={"fontWeight": "700", "fontSize": "12px", "lineHeight": "1.2"}),
                            html.Div(f"{cnt} messages", style={"fontSize": "11px", "opacity": 0.75}),
                        ],
                        id={"type": "chat-session-btn", "index": sid},
                        n_clicks=0,
                        style={
                            "width": "100%",
                            "textAlign": "left",
                            "border": "1px solid #e8ecf6",
                            "borderRadius": "12px",
                            "padding": "10px 10px",
                            "marginBottom": "8px",
                            "background": "#EAF3FF" if is_active else "white",
                            "cursor": "pointer",
                        },
                    )
                )
            if not items:
                items = [html.Div("Aucune conversation pour le moment.", style={"fontSize": "12px", "opacity": 0.7})]
            return items

        # Ensure session exists
        if not session_id and mem:
            try:
                session_id = mem.create_session()
            except Exception:
                session_id = None

        # -------------------------
        # Case: upload image -> preview only
        # -------------------------
        if trigger == "chat-image-upload":
            raw, mime, preview_src = _safe_decode_upload(upload_contents)
            if raw is None:
                return (
                    current_messages,
                    history,
                    "Image invalide (format non supporté).",
                    None,
                    "",
                    no_update,
                    "",
                    no_update,
                    session_id,
                    sessions_store,
                    _render_sessions_list(_refresh_sessions(), session_id),
                )

            # preview thumbnail
            preview = html.Img(src=preview_src, style={"maxWidth": "100%", "borderRadius": "10px"})
            return (
                current_messages,
                history,
                "",
                raw,
                "",
                no_update,
                preview,
                no_update,
                session_id,
                sessions_store,
                _render_sessions_list(_refresh_sessions(), session_id),
            )

        # -------------------------
        # Case: new chat
        # -------------------------
        if trigger == "chat-new-chat-btn":
            if mem:
                try:
                    session_id = mem.create_session()
                except Exception:
                    session_id = None
            # reset UI
            sessions_store = _refresh_sessions()
            return (
                [_greeting_bubble()],
                [],
                "",
                None,
                "",
                "",
                "",
                None,
                session_id,
                sessions_store,
                _render_sessions_list(sessions_store, session_id),
            )

        # -------------------------
        # Case: switch session
        # -------------------------
        if trigger.startswith("{") and "chat-session-btn" in trigger:
            try:
                trig = json.loads(trigger)
                target_sid = trig.get("index")
            except Exception:
                target_sid = None

            if mem and target_sid:
                sess = mem.get_session(target_sid)
                if sess:
                    # Convert stored messages into our lightweight history format
                    msgs = []
                    for m in sess.messages or []:
                        role = m.get("role")
                        text = m.get("text", "")
                        meta = m.get("metadata") or {}
                        # If metadata contains zone_info -> keep it
                        msgs.append({"role": role, "text": text, "metadata": meta})
                    sessions_store = _refresh_sessions()
                    return (
                        _render_history(msgs),
                        [{"role": m["role"], "text": m["text"]} for m in msgs],
                        "",
                        None,
                        "",
                        "",
                        "",
                        None,
                        target_sid,
                        sessions_store,
                        _render_sessions_list(sessions_store, target_sid),
                    )

            # fallback: no change
            return (
                current_messages,
                history,
                "",
                None,
                "",
                no_update,
                no_update,
                no_update,
                session_id,
                sessions_store,
                _render_sessions_list(_refresh_sessions(), session_id),
            )

        # -------------------------
        # Case: click suggestion button
        # -------------------------
        if trigger.startswith("{") and "chat-suggestion-btn" in trigger:
            try:
                trig = json.loads(trigger)
                # Dash trigger id contains our dict; query is inside
                # but Dash serializes dict keys as provided.
                suggested_query = trig.get("index")
            except Exception:
                suggested_query = None

            if suggested_query and str(suggested_query).strip():
                user_text = str(suggested_query).strip()
                # On continue comme si c'était un envoi
                trigger = "chat-send-btn"
            else:
                return (
                    current_messages,
                    history,
                    "Suggestion invalide.",
                    image_bytes_store,
                    "",
                    no_update,
                    no_update,
                    no_update,
                    session_id,
                    sessions_store,
                    _render_sessions_list(_refresh_sessions(), session_id),
                )

# -------------------------
        # Case: send message (button or enter)
        # -------------------------
        if trigger not in ("chat-send-btn", "chat-input"):
            # unknown trigger
            return (
                current_messages,
                history,
                "",
                image_bytes_store,
                "",
                no_update,
                no_update,
                no_update,
                session_id,
                sessions_store,
                _render_sessions_list(_refresh_sessions(), session_id),
            )

        if not user_text or not str(user_text).strip():
            return (
                current_messages,
                history,
                "Veuillez écrire un message.",
                image_bytes_store,
                "",
                no_update,
                no_update,
                no_update,
                session_id,
                sessions_store,
                _render_sessions_list(_refresh_sessions(), session_id),
            )

        user_text = str(user_text).strip()

        # Persist user message
        if mem and session_id:
            try:
                mem.add_message(session_id, "user", user_text, metadata={})
            except Exception:
                pass

        # Add user bubble
        current_messages = list(current_messages)
        current_messages.append(_user_bubble(user_text))

        # Call backend
        mime_type = "image/jpeg"
        bot_answer = ""
        zone_info = None
        suggestions = []
        try:
            bot_answer, zone_info, suggestions = generate_chat_response(
                history=history,
                user_message=user_text,
                image_bytes=image_bytes_store,
                mime_type=mime_type,
            )

        except Exception as e:
            return (
                current_messages,
                history,
                f"Erreur lors de l'appel au service IA : {e}",
                None,
                "",
                "",
                "",
                no_update,
                session_id,
                _refresh_sessions(),
                _render_sessions_list(_refresh_sessions(), session_id),
            )

        # Add bot message to store history
        history = list(history)
        history.append({"role": "user", "text": user_text})
        history.append({"role": "model", "text": bot_answer})

        # Map payload (compatible + enrichi)
        map_action_payload = None
        # On déclenche une action carte dès qu'on a (page) OU (coords) OU (nom).
        # Ça évite le cas où le bot détecte le thème/coords mais n'a pas "name".
        if zone_info and isinstance(zone_info, dict) and (
            zone_info.get("page")
            or (zone_info.get("lat") is not None and zone_info.get("lon") is not None)
            or zone_info.get("name")
        ):
            map_action_payload = {
                "type": zone_info.get("type"),
                "name": zone_info.get("name"),
                "idpoint": zone_info.get("idpoint"),
            }

            # ✅ Page / layer (pour router vers la bonne carte)
            if zone_info.get("page"):
                map_action_payload["page"] = zone_info.get("page")
            if zone_info.get("focus_type"):
                map_action_payload["focus_type"] = zone_info.get("focus_type")
            if zone_info.get("metrics"):
                map_action_payload["metrics"] = zone_info.get("metrics")
            if zone_info.get("layer"):
                map_action_payload["layer"] = zone_info.get("layer")

            # Enrich coords (dashboard peut ignorer si non utilisé)
            if zone_info.get("lat") is not None and zone_info.get("lon") is not None:
                map_action_payload["lat"] = zone_info.get("lat")
                map_action_payload["lon"] = zone_info.get("lon")
                map_action_payload["zoom"] = zone_info.get("zoom", 14)

        # Persist bot message + metadata
        if mem and session_id:
            try:
                meta = {}
                if zone_info:
                    meta["zone_info"] = zone_info
                if suggestions:
                    meta["suggestions"] = suggestions
                mem.add_message(session_id, "model", bot_answer, metadata=meta)
            except Exception:
                pass

        current_messages.append(_bot_bubble(bot_answer, zone_info=zone_info, suggestions=suggestions))

        sessions_store = _refresh_sessions()
        sessions_list_children = _render_sessions_list(sessions_store, session_id)

        # Reset image & input & preview
        return (
            current_messages,
            history,
            "",
            None,
            "",
            "",
            "",
            map_action_payload,
            session_id,
            sessions_store,
            sessions_list_children,
        )


    # 4) Ouvrir/fermer le MODAL (carte + indicateurs) selon chat-map-action
    @app.callback(
        Output("map-modal", "is_open"),
        Output("map-modal-iframe", "src"),
        Input("chat-map-action", "data"),
        Input("map-modal-close", "n_clicks"),
        State("map-modal", "is_open"),
        prevent_initial_call=True,
    )
    def open_close_map_modal(map_action, n_close, is_open):
        ctx = dash.callback_context
        trigger = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else ""

        if trigger == "map-modal-close":
            return False, ""

        if not isinstance(map_action, dict):
            return no_update, no_update

        if (map_action.get("page") or "").strip().lower() != "map-focus":
            return no_update, no_update

        from urllib.parse import urlencode

        params = {
            "name": map_action.get("name", ""),
            "focus_type": map_action.get("focus_type", "situation"),
        }

        if map_action.get("lat") is not None and map_action.get("lon") is not None:
            params["lat"] = map_action.get("lat")
            params["lon"] = map_action.get("lon")
            params["zoom"] = map_action.get("zoom", 12)

        if map_action.get("metrics"):
            try:
                params["metrics"] = json.dumps(map_action.get("metrics"), ensure_ascii=False)
            except Exception:
                pass

        src = "/assets/map_focus_minimal.html?" + urlencode(params)
        return True, src
