from __future__ import annotations

import os
from urllib.parse import parse_qs

import mysql.connector
from dash import html, Input, Output, State, no_update, clientside_callback


def _connect():
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST", os.environ.get("MYSQL_HOST", "db")),
        user=os.environ.get("DB_USER", os.environ.get("MYSQL_USER", "root")),
        password=os.environ.get("DB_PASSWORD", os.environ.get("MYSQL_PASSWORD", "rootpassword")),
        database=os.environ.get("DB_NAME", os.environ.get("MYSQL_DATABASE", "projet_solarx")),
        charset="utf8",
    )


def _safe_float(x):
    try:
        if x is None:
            return None
        if isinstance(x, str):
            x = x.replace(",", ".").strip()
        return float(x)
    except Exception:
        return None


def _metric_row(icon, label, value, highlight=False):
    return html.Div(
        style={
            "display": "flex",
            "alignItems": "baseline",
            "justifyContent": "space-between",
            "padding": "10px 10px",
            "borderRadius": "10px",
            "background": "#FFF7F1" if highlight else "#F7F9FC",
            "border": "1px solid #EAEFF6",
            "marginBottom": "8px",
        },
        children=[
            html.Div(f"{icon} {label}", style={"fontWeight": "700", "color": "#223"}),
            html.Div(value, style={"fontWeight": "700", "color": "#111"}),
        ],
    )


def register_map_focus_callbacks(app):
    """
    Page /map-focus :
    - Lit lat/lon/zoom + name + focus_type (depuis URL et/ou chat-map-action)
    - Trouve le point GPS le plus proche
    - Récupère la dernière mesure
    - Remplit le panneau d'infos (focus-info-panel)
    - Remplit focus-location-store avec toutes les métriques
    - Envoie automatiquement un postMessage à l'iframe map-focus-iframe pour zoom + marker rouge + popup
    """

    # ---------------------------------------------------------------------
    # 0) Client-side: quand focus-location-store change -> postMessage à l'iframe
    # ---------------------------------------------------------------------
    # NOTE: Ton layout doit contenir html.Div(id="map-focus-dummy", style={"display":"none"})
    clientside_callback(
        """
        function(payload){
          if(!payload) return window.dash_clientside.no_update;
          const iframe = document.getElementById("map-focus-iframe");
          if(!iframe || !iframe.contentWindow) return window.dash_clientside.no_update;

          // On envoie FOCUS_TO (ou ZOOM_TO) à la carte HTML Leaflet
          iframe.contentWindow.postMessage({type:"FOCUS_TO", payload: payload}, "*");
          return null;
        }
        """,
        Output("map-focus-dummy", "children"),
        Input("focus-location-store", "data"),
    )

    # ---------------------------------------------------------------------
    # 1) Stocker la dernière action chat destinée à map-focus
    # ---------------------------------------------------------------------
    @app.callback(
        Output("focus-location-store", "data"),
        Input("chat-map-action", "data"),
        prevent_initial_call=True,
    )
    def _store_focus(action_data):
        if not isinstance(action_data, dict):
            return no_update
        if (action_data.get("page") or "").strip().lower() != "map-focus":
            return no_update
        # On stocke l'action, mais elle sera enrichie par le callback panel ci-dessous
        return action_data

    # ---------------------------------------------------------------------
    # 2) Quand on est sur /map-focus -> construire panneau + enrichir store
    # ---------------------------------------------------------------------
    @app.callback(
        Output("focus-info-panel", "children"),
        Output("focus-location-store", "data", allow_duplicate=True),
        Input("url", "pathname"),
        Input("url", "search"),
        State("focus-location-store", "data"),
        prevent_initial_call=False,
    )
    def _render_focus_panel(pathname, search, stored_action):
        if pathname != "/map-focus":
            return no_update, no_update

        stored_action = stored_action if isinstance(stored_action, dict) else {}

        qs = parse_qs((search or "").lstrip("?"))

        def _get_qs(key):
            v = qs.get(key)
            return v[0] if v else None

        # Priorité à l'URL, sinon store
        lat = _safe_float(_get_qs("lat")) or _safe_float(stored_action.get("lat"))
        lon = _safe_float(_get_qs("lon")) or _safe_float(stored_action.get("lon"))
        zoom = _safe_float(_get_qs("zoom")) or _safe_float(stored_action.get("zoom")) or 13
        name = _get_qs("name") or stored_action.get("name") or ""
        focus_type = (_get_qs("focus") or stored_action.get("focus_type") or "situation").strip().lower()

        if lat is None or lon is None:
            panel = html.Div("Aucune coordonnée fournie pour afficher le focus.", style={"color": "#c0392b"})
            return panel, no_update

        # Trouver le point GPS le plus proche + dernière mesure
        conn = _connect()
        try:
            cur = conn.cursor(dictionary=True, buffered=True)

            cur.execute(
                """
                SELECT idpoint, latitude, longitude, adresse
                FROM 2026_solarx_pointsgps
                ORDER BY (POWER(latitude - %s, 2) + POWER(longitude - %s, 2)) ASC
                LIMIT 1
                """,
                (lat, lon),
            )
            pt = cur.fetchone() or {}
            idpoint = pt.get("idpoint")
            adresse = pt.get("adresse") or "Adresse inconnue"

            last = {}
            if idpoint is not None:
                cur.execute(
                    """
                    SELECT temperature, ensoleillement, irradiance, precipitation, date_collecte
                    FROM 2026_solarx_mesures
                    WHERE idpoint = %s
                    ORDER BY date_collecte DESC
                    LIMIT 1
                    """,
                    (idpoint,),
                )
                last = cur.fetchone() or {}

            temp = _safe_float(last.get("temperature"))
            ens_s = _safe_float(last.get("ensoleillement"))
            irr = _safe_float(last.get("irradiance"))
            prec = _safe_float(last.get("precipitation"))
            date_collecte = last.get("date_collecte") or "N/A"

            # Conversions
            ens_h = (ens_s / 3600.0) if ens_s is not None else None
            # Estimation simple production (tu peux changer la règle)
            prod = (irr * 365.0 * 3.0) if irr is not None else None  # ~3 kW sur 1 an

            header = html.Div(
                style={"marginBottom": "10px"},
                children=[
                    html.Div(
                        f"Zone : {name}" if name else "Zone sélectionnée",
                        style={"fontSize": "16px", "fontWeight": "800", "marginBottom": "4px"},
                    ),
                    html.Div(
                        f"Point GPS : {idpoint}" if idpoint is not None else "Point GPS : N/A",
                        style={"fontSize": "12px", "color": "#555"},
                    ),
                    html.Div(f"Adresse : {adresse}", style={"fontSize": "12px", "color": "#555"}),
                    html.Div(
                        f"Dernière collecte : {date_collecte}",
                        style={"fontSize": "12px", "color": "#777", "marginTop": "4px"},
                    ),
                ],
            )

            rows = [
                _metric_row(
                    "☀️",
                    "Ensoleillement",
                    f"{ens_h:.2f} h/j" if ens_h is not None else "N/A",
                    highlight=focus_type == "ensoleillement",
                ),
                _metric_row(
                    "🔆",
                    "Irradiance",
                    f"{irr:.2f} kWh/m²" if irr is not None else "N/A",
                    highlight=focus_type in ("irradiance", "ensoleillement", "production"),
                ),
                _metric_row(
                    "⚡",
                    "Production",
                    f"{prod:.0f} kWh" if prod is not None else "N/A",
                    highlight=focus_type == "production",
                ),
                _metric_row(
                    "🌧️",
                    "Précipitations",
                    f"{prec:.2f} mm" if prec is not None else "N/A",
                    highlight=focus_type == "precipitation",
                ),
                _metric_row(
                    "🌡️",
                    "Température",
                    f"{temp:.2f} °C" if temp is not None else "N/A",
                    highlight=focus_type == "temperature",
                ),
            ]

            panel_children = [header] + rows

            # ✅ Payload complet pour la carte (marker rouge + popup auto)
            enriched_store = {
                **stored_action,
                "page": "map-focus",
                "lat": float(lat),
                "lon": float(lon),
                "zoom": int(zoom) if zoom is not None else 13,
                "name": name,
                "address": adresse,
                "idpoint": idpoint,
                "date_collecte": date_collecte,
                "temperature": temp,
                "precipitation": prec,
                "irradiance": irr,
                "ensoleillement": ens_h,   # en h/j pour l'affichage popup
                "production": prod,
                "focus_type": focus_type,
            }

            return panel_children, enriched_store

        except Exception as e:
            panel = html.Div(f"Erreur lors du chargement des infos: {e}", style={"color": "#c0392b"})
            return panel, no_update
        finally:
            try:
                conn.close()
            except Exception:
                pass

    # ---------------------------------------------------------------------
    # 3) Bouton: voir zones industrielles proches (déclenche navigation via chat-map-action)
    # ---------------------------------------------------------------------
    @app.callback(
        Output("chat-map-action", "data", allow_duplicate=True),
        Input("focus-nearby-industrial-btn", "n_clicks"),
        State("focus-location-store", "data"),
        prevent_initial_call=True,
    )
    def _go_industrial(n_clicks, action_data):
        if not n_clicks:
            return no_update
        if not isinstance(action_data, dict):
            return no_update

        lat = action_data.get("lat")
        lon = action_data.get("lon")
        zoom = action_data.get("zoom", 13)
        name = action_data.get("name", "")

        if lat is None or lon is None:
            return no_update

        return {
            "action": "zoom",
            "page": "zones-industrielles",
            "layer": "zones-industrielles",
            "type": action_data.get("type") or "commune",
            "name": name,
            "lat": lat,
            "lon": lon,
            "zoom": zoom,
        }
