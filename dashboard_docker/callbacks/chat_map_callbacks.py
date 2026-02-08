"""callbacks/chat_map_callbacks.py

Callbacks "Chat -> Map" - Version améliorée avec zoom via URL params.

NOUVEAUTÉS:
- Navigation avec paramètres URL (?lat=X&lon=Y&zoom=Z)
- PostMessage vers les iframes Leaflet pour zoom en temps réel
- Support de tous les types de cartes (ensoleillement, température, etc.)
- Animation de zoom fluide
- Historique de navigation

Attendu dans chat-map-action (dict):
{
  "action": "zoom",
  "lat": 46.2,
  "lon": 6.15,
  "zoom": 12,
  "page": "electricite" | "optimisation" | "ensoleillement" | "temperature" | "precipitation" | "zones-industrielles" | "production",
  "layer": "ensoleillement" | "temperature" | ...,
  "name": "Nom du lieu",
  "idpoint": 123  (optionnel)
}
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlencode

from dash import Input, Output, State, no_update, callback_context, clientside_callback


# ============================================================================
#  MAPPING DES PAGES ET LAYERS
# ============================================================================

PAGE_ROUTE_MAP = {
    "electricite": "/electricite",
    "consommation": "/electricite",
    "optimisation": "/optimisation",
    "production": "/production",
    "ensoleillement": "/ensoleillement",
    "temperature": "/temperature",
    "precipitation": "/precipitation",
    "precipitations": "/precipitation",
    "zones_industrielles": "/zones-industrielles",
    "zones-industrielles": "/zones-industrielles",
    "zone_industrielle": "/zones-industrielles",
    "industriel": "/zones-industrielles",
}

LAYER_IFRAME_MAP = {
    "ensoleillement": "map-ensoleillement-iframe",
    "temperature": "map-temperature-iframe",
    "precipitation": "map-precipitation-iframe",
    "precipitations": "map-precipitation-iframe",
    "production": "map-production-iframe",
    "optimisation": "map-optimisation-iframe",
    "zones_industrielles": "map-zones-iframe",
    "zones-industrielles": "map-zones-iframe",
    "electricite": "map-electricite",  # Plotly map
}


def _build_url_with_coords(base_path: str, lat: float, lon: float, zoom: int = 13, name: str = None) -> str:
    """Construit une URL avec les paramètres de coordonnées."""
    params = {
        "lat": f"{lat:.6f}",
        "lon": f"{lon:.6f}",
        "zoom": str(zoom),
    }
    if name:
        params["name"] = name
    return f"{base_path}?{urlencode(params)}"


def _get_first_coord_from_geojson(geojson: Dict[str, Any]) -> Optional[Tuple[float, float]]:
    """Retourne (lat, lon) à partir d'un geojson FeatureCollection."""
    try:
        feats = geojson.get("features") or []
        if not feats:
            return None
        geom = (feats[0] or {}).get("geometry") or {}
        gtype = geom.get("type")
        coords = geom.get("coordinates")
        if not coords:
            return None

        if gtype == "Polygon":
            lon, lat = coords[0][0]
            return float(lat), float(lon)
        if gtype == "MultiPolygon":
            lon, lat = coords[0][0][0]
            return float(lat), float(lon)
        if gtype == "Point":
            lon, lat = coords
            return float(lat), float(lon)
    except Exception:
        return None
    return None


def _apply_zoom_to_plotly_figure(fig: Any, lat: float, lon: float, zoom: float) -> Any:
    """Applique center/zoom sur une figure Plotly (mapbox ou geo)."""
    if fig is None:
        return no_update

    try:
        new_fig = fig.to_plotly_json() if hasattr(fig, "to_plotly_json") else fig
    except Exception:
        new_fig = fig

    if not isinstance(new_fig, dict):
        return no_update

    layout = new_fig.setdefault("layout", {})
    if not isinstance(layout, dict):
        return no_update

    applied = False

    # Mapbox
    mapbox_keys = [k for k in layout.keys() if str(k).startswith("mapbox")]
    if not mapbox_keys and "mapbox" in layout:
        mapbox_keys = ["mapbox"]
    for k in mapbox_keys:
        mb = layout.setdefault(k, {})
        if isinstance(mb, dict):
            mb["center"] = {"lat": float(lat), "lon": float(lon)}
            mb["zoom"] = float(zoom)
            applied = True

    # Geo
    geo_keys = [k for k in layout.keys() if str(k).startswith("geo")]
    if not geo_keys and "geo" in layout:
        geo_keys = ["geo"]
    for k in geo_keys:
        g = layout.setdefault(k, {})
        if isinstance(g, dict):
            g.setdefault("center", {})
            if isinstance(g.get("center"), dict):
                g["center"]["lat"] = float(lat)
                g["center"]["lon"] = float(lon)
            g["projection"] = g.get("projection") or {"type": "mercator"}
            scale = max(1.0, min(10.0, float(zoom) / 2.0))
            if isinstance(g.get("projection"), dict):
                g["projection"]["scale"] = scale
            applied = True

    return new_fig if applied else no_update


def register_chat_map_callbacks(app, communes_geo_data=None, **_kwargs):
    """
    Enregistre les callbacks de navigation chat -> carte.
    
    Parameters
    ----------
    app: dash.Dash
    communes_geo_data: GeoJSON des communes (FeatureCollection)
    """

    # =========================================================================
    # 1) Navigation avec URL params (lat, lon, zoom)
    # =========================================================================
    @app.callback(
        Output("url", "pathname", allow_duplicate=True),
        Output("url", "search", allow_duplicate=True),
        Input("chat-map-action", "data"),
        State("url", "pathname"),
        prevent_initial_call=True,
    )
    def navigate_with_coords(action_data, current_path):
        """Navigation vers la page cible avec coordonnées en URL params."""
        if not action_data or not isinstance(action_data, dict):
            return no_update, no_update

        lat = action_data.get("lat")
        lon = action_data.get("lon")
        zoom = action_data.get("zoom", 13)
        page = (action_data.get("page") or "").strip().lower()
        name = action_data.get("name") or ""

        # Déterminer la route
        target_path = PAGE_ROUTE_MAP.get(page)
        if not target_path:
            # Fallback: si type commune -> electricite
            if action_data.get("type") == "commune":
                target_path = "/electricite"
            else:
                return no_update, no_update

        # Construire les query params
        search_params = ""
        if lat is not None and lon is not None:
            params = {"lat": f"{lat:.6f}", "lon": f"{lon:.6f}", "zoom": str(int(zoom))}
            if name:
                params["name"] = name
            search_params = "?" + urlencode(params)

        # Si déjà sur la bonne page, on met juste à jour les params
        if current_path == target_path and not search_params:
            return no_update, no_update

        return target_path, search_params

    # =========================================================================
    # 2) Zoom sur carte Plotly (pour /electricite)
    # =========================================================================
    @app.callback(
        Output("map-graph", "figure", allow_duplicate=True),
        Input("chat-map-action", "data"),
        State("map-graph", "figure"),
        prevent_initial_call=True,
    )
    def zoom_plotly_map(action_data, fig):
        """Zoom sur la carte Plotly (électricité/consommation)."""
        if not action_data or not isinstance(action_data, dict):
            return no_update

        lat = action_data.get("lat")
        lon = action_data.get("lon")
        zoom = action_data.get("zoom", 12)

        if lat is not None and lon is not None:
            return _apply_zoom_to_plotly_figure(fig, float(lat), float(lon), float(zoom))

        # Fallback: chercher dans communes_geo_data
        commune = action_data.get("commune") or action_data.get("name")
        if commune and isinstance(communes_geo_data, dict):
            cname = str(commune).strip().lower()
            for feat in communes_geo_data.get("features") or []:
                props = (feat or {}).get("properties") or {}
                nm = props.get("name") or props.get("nom") or props.get("commune")
                if nm and str(nm).strip().lower() == cname:
                    geom = feat.get("geometry") or {}
                    tmp = {"features": [{"geometry": geom}]}
                    pt = _get_first_coord_from_geojson(tmp)
                    if pt:
                        return _apply_zoom_to_plotly_figure(fig, pt[0], pt[1], float(zoom))

        return no_update

    # =========================================================================
    # 3) Store les coords pour les iframes Leaflet
    # =========================================================================
    @app.callback(
        Output("map-zoom-coords-store", "data", allow_duplicate=True),
        Input("chat-map-action", "data"),
        prevent_initial_call=True,
    )
    def store_zoom_coords(action_data):
        """Stocke les coordonnées pour transmission aux iframes."""
        if not action_data or not isinstance(action_data, dict):
            return no_update

        lat = action_data.get("lat")
        lon = action_data.get("lon")
        zoom = action_data.get("zoom", 13)
        name = action_data.get("name")
        idpoint = action_data.get("idpoint")
        page = action_data.get("page") or action_data.get("layer")

        if lat is None or lon is None:
            return no_update

        return {
            "lat": float(lat),
            "lon": float(lon),
            "zoom": int(zoom),
            "name": name,
            "idpoint": idpoint,
            "page": page,
            "timestamp": str(__import__("datetime").datetime.now().isoformat()),
        }

    # =========================================================================
    # 4) Clientside callback pour envoyer postMessage aux iframes
    # =========================================================================
    app.clientside_callback(
        """
        function(coordsData, pathname) {
            if (!coordsData || !coordsData.lat || !coordsData.lon) {
                return window.dash_clientside.no_update;
            }
            
            // Identifier tous les iframes de carte
            const iframeIds = [
                'map-ensoleillement-iframe',
                'map-temperature-iframe',
                'map-precipitation-iframe',
                'map-production-iframe',
                'map-optimisation-iframe',
                'map-zones-iframe'
            ];
            
            // Envoyer postMessage à chaque iframe trouvé
            iframeIds.forEach(function(id) {
                const iframe = document.getElementById(id);
                if (iframe && iframe.contentWindow) {
                    try {
                        iframe.contentWindow.postMessage({
                            type: 'ZOOM_TO',
                            lat: coordsData.lat,
                            lon: coordsData.lon,
                            zoom: coordsData.zoom || 13,
                            label: coordsData.name || '',
                            idpoint: coordsData.idpoint || null
                        }, '*');
                    } catch(e) {
                        console.warn('PostMessage failed for', id, e);
                    }
                }
            });
            
            // Retourner timestamp pour confirmer l'exécution
            return new Date().toISOString();
        }
        """,
        Output("map-zoom-timestamp", "data"),
        Input("map-zoom-coords-store", "data"),
        State("url", "pathname"),
    )

    # =========================================================================
    # 5) Parse URL params au chargement de page
    # =========================================================================
    @app.callback(
        Output("map-zoom-coords-store", "data", allow_duplicate=True),
        Input("url", "search"),
        State("url", "pathname"),
        prevent_initial_call=True,
    )
    def parse_url_coords(search, pathname):
        """Parse les coordonnées depuis les URL params."""
        if not search or not search.strip("?"):
            return no_update

        from urllib.parse import parse_qs
        params = parse_qs(search.lstrip("?"))

        lat = params.get("lat", [None])[0]
        lon = params.get("lon", [None])[0]
        zoom = params.get("zoom", ["13"])[0]
        name = params.get("name", [""])[0]

        if lat and lon:
            try:
                return {
                    "lat": float(lat),
                    "lon": float(lon),
                    "zoom": int(zoom),
                    "name": name,
                    "page": pathname.strip("/"),
                    "from_url": True,
                }
            except (ValueError, TypeError):
                pass

        return no_update


def register_additional_stores(app):
    """
    Enregistre les dcc.Store supplémentaires nécessaires.
    À appeler dans dashboard.py après la création de l'app.
    """
    from dash import dcc, html

    return [
        dcc.Store(id="map-zoom-coords-store", storage_type="memory"),
        dcc.Store(id="map-zoom-timestamp", storage_type="memory"),
        dcc.Store(id="map-navigation-history", storage_type="session", data=[]),
    ]
