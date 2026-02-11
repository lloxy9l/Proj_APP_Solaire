# layouts/map_focus.py
# ✅ Compatible avec ton projet (router manuel) : PAS de dash.register_page()

from urllib.parse import parse_qs
from dash import html, dcc

# On réutilise tes helpers DB (ajoutés dans services/chat_service.py)
# IMPORTANT : ces fonctions existent dans chat_service_MODIFIED.py fourni.
from services.chat_service import (
    _find_point_by_name_like,
    _find_zone_origin_by_name_like,
    _fetch_latest_metrics_for_point,
)


def _resolve_location(name: str):
    """Retourne (lat, lon, label, idpoint|None) via pointsGPS puis zones."""
    name = (name or "").strip()
    if not name:
        return None

    pt = _find_point_by_name_like(name)
    if pt:
        return float(pt["lat"]), float(pt["lon"]), pt.get("label", name), pt.get("idpoint")

    z = _find_zone_origin_by_name_like(name)
    if z:
        return float(z["lat"]), float(z["lon"]), z.get("label", name), None

    return None


def _route_for_focus(focus_type: str) -> str:
    focus_type = (focus_type or "situation").lower().strip()
    # Adapte si tes routes sont différentes
    if focus_type == "precipitation":
        return "/precipitation"
    if focus_type == "ensoleillement":
        return "/ensoleillement"
    if focus_type == "temperature":
        return "/temperature"
    return "/temperature"


def _metric_line(title, value, unit=""):
    if value is None or value == "":
        value = "-"
    return html.Div(
        [
            html.Div(title, style={"fontSize": "12px", "opacity": 0.75}),
            html.Div(f"{value}{unit}", style={"fontSize": "16px", "fontWeight": "800"}),
        ],
        style={"padding": "10px", "background": "#f7f9ff", "borderRadius": "12px"},
    )


def render_map_focus(search: str):
    """
    À appeler depuis ton router (dashboard.py) quand pathname == '/map-focus'
    Exemple:
        if pathname == "/map-focus":
            return render_map_focus(search)
    """
    qs = parse_qs((search or "").lstrip("?"))
    name = (qs.get("name", [""]) or [""])[0]
    focus_type = (qs.get("focus_type", ["situation"]) or ["situation"])[0]

    # coords explicites (si déjà passées)
    lat = qs.get("lat", [None])[0]
    lon = qs.get("lon", [None])[0]
    zoom = qs.get("zoom", [12])[0]

    label = name
    idpoint = None

    if lat is not None and lon is not None:
        try:
            lat = float(lat)
            lon = float(lon)
        except Exception:
            lat = None
            lon = None

    if lat is None or lon is None:
        resolved = _resolve_location(name)
        if resolved:
            lat, lon, label, idpoint = resolved

    if lat is None or lon is None:
        return html.Div(
            "Impossible de localiser ce lieu dans la base SolarX.",
            style={"padding": "12px", "background": "#fff", "borderRadius": "12px"},
        )

    try:
        zoom = int(float(zoom))
    except Exception:
        zoom = 12

    # métriques si point
    metrics = _fetch_latest_metrics_for_point(int(idpoint)) if idpoint else None
    metrics = metrics or {}

    left_route = _route_for_focus(focus_type)
    iframe_src = f"{left_route}?lat={lat}&lon={lon}&zoom={zoom}&name={label}"

    return html.Div(
        style={"padding": "14px"},
        children=[
            dcc.Location(id="mf-url"),  # optionnel, mais garde cohérence layout
            html.Div(
                style={"display": "grid", "gridTemplateColumns": "1.5fr 1fr", "gap": "12px"},
                children=[
                    html.Div(
                        style={
                            "background": "#fff",
                            "borderRadius": "14px",
                            "overflow": "hidden",
                            "border": "1px solid #eef1f7",
                        },
                        children=[
                            html.Div(
                                f"🗺️ {label}",
                                style={
                                    "padding": "10px 12px",
                                    "fontWeight": "800",
                                    "borderBottom": "1px solid #eef1f7",
                                },
                            ),
                            html.Iframe(
                                src=iframe_src,
                                style={"width": "100%", "height": "520px", "border": "0"},
                            ),
                        ],
                    ),
                    html.Div(
                        style={
                            "background": "#fff",
                            "borderRadius": "14px",
                            "border": "1px solid #eef1f7",
                            "padding": "12px",
                        },
                        children=[
                            html.Div("📊 Indicateurs (dernier relevé)", style={"fontWeight": "900", "marginBottom": "10px"}),
                            html.Div(
                                style={"display": "grid", "gridTemplateColumns": "1fr", "gap": "10px"},
                                children=[
                                    _metric_line("Température", metrics.get("temperature"), " °C"),
                                    _metric_line("Précipitations", metrics.get("precipitation"), " mm"),
                                    _metric_line("Irradiance", metrics.get("irradiance"), " kWh/m²/j"),
                                    _metric_line("Ensoleillement", metrics.get("ensoleillement_h"), " h"),
                                    _metric_line("Date collecte", metrics.get("date_collecte"), ""),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )
