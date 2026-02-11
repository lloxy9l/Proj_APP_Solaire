
from __future__ import annotations

import io
import json
from typing import Any

from dash import html, dcc, Input, Output, State, no_update, callback_context
from dash.dependencies import ALL
import dash_bootstrap_components as dbc


# =========================
# Helpers (score + UI)
# =========================
def _safe_float(x, default=None):
    try:
        if x is None:
            return default
        return float(x)
    except Exception:
        return default


def _compute_score_global(p: dict) -> float | None:
    sg = _safe_float(p.get("score_global"))
    return sg


def _pill(text: str, color_bg="rgba(0,93,255,0.10)", color_fg="#005DFF"):
    return html.Span(
        text,
        style={
            "display": "inline-flex",
            "align-items": "center",
            "gap": "6px",
            "padding": "6px 10px",
            "border-radius": "999px",
            "font-size": "12px",
            "font-weight": "700",
            "border": "1px solid rgba(0,0,0,0.10)",
            "background": color_bg,
            "color": color_fg,
            "white-space": "nowrap",
        },
    )


def _metric(label: str, value: str, icon: str):
    return html.Div(
        style={"display": "flex", "align-items": "center", "gap": "6px", "font-size": "12px", "color": "#333"},
        children=[
            html.Span(icon, style={"font-size": "12px"}),
            html.Span(f"{label} : ", style={"color": "#666"}),
            html.Span(value, style={"font-weight": "700"}),
        ],
    )


def _format_point_card(p: dict, rank: int):
    sg = _compute_score_global(p)
    sg_txt = f"{sg:.1f} %" if sg is not None else "N/A"

    idpoint = p.get("idpoint") or p.get("id") or p.get("ID") or "?"
    pid = str(idpoint)
    adresse = p.get("adresse") or "Adresse inconnue"

    ens = _safe_float(p.get("ensoleillement"))
    irr = _safe_float(p.get("irradiance"))
    prod = _safe_float(p.get("production"))
    temp = _safe_float(p.get("temperature"))

    lat = _safe_float(p.get("latitude"))
    lon = _safe_float(p.get("longitude"))

    badge = _pill("🥇 Meilleur emplacement", "rgba(255,180,0,0.18)", "#A55B00") if rank == 0 else None

    header_left = html.Div(
        style={"display": "flex", "align-items": "center", "gap": "8px"},
        children=[
            html.Span(f"ID Point {pid}", style={"font-weight": "800", "font-size": "13px"}),
            badge if badge else html.Span(),
        ],
    )

    header_right = html.Div(
        style={"display": "flex", "align-items": "center", "gap": "10px"},
        children=[
            html.Span(sg_txt, style={"font-weight": "900", "color": "#0A8A4B", "font-size": "14px"}),
            dbc.Button(
                "⚖️",
                id={"type": "opt-compare-btn", "index": pid},
                n_clicks=0,
                size="sm",
                color="light",
                style={"border-radius": "10px", "padding": "2px 8px", "font-size": "12px"},
                title="Comparer (sélectionner 2 points)",
            ),
        ],
    )

    latlon_row = html.Div(
        style={"display": "flex", "align-items": "center", "justify-content": "space-between", "gap": "8px"},
        children=[
            html.Div(
                style={"font-size": "11px", "color": "#555"},
                children=[
                    html.Span("📍 "),
                    html.Span(f"{lat:.5f}, {lon:.5f}" if (lat is not None and lon is not None) else "Lat/Lon N/A"),
                ],
            ),
            dbc.Button(
                "📋 Copier",
                id={"type": "opt-copy-btn", "index": pid},
                n_clicks=0,
                size="sm",
                color="light",
                style={"border-radius": "10px", "padding": "2px 8px", "font-size": "12px"},
                title="Copier lat/lon dans le presse-papiers",
            ),
        ],
    )

    return dbc.Card(
        id={"type": "opt-point-card", "index": pid},
        style={
            "border-radius": "16px",
            "border": "1px solid #e6ecff",
            "box-shadow": "0 6px 14px rgba(0,0,0,0.06)",
            "margin-bottom": "10px",
            "overflow": "hidden",
        },
        children=[
            dbc.CardBody(
                style={"padding": "12px"},
                children=[
                    html.Div(
                        style={"display": "flex", "align-items": "center", "justify-content": "space-between"},
                        children=[header_left, header_right],
                    ),
                    html.Div(adresse, style={"font-size": "11px", "color": "#666", "margin-top": "4px"}),
                    html.Div(style={"height": "8px"}),
                    latlon_row,
                    html.Div(style={"height": "8px"}),
                    html.Div(
                        style={"display": "grid", "grid-template-columns": "1fr 1fr", "gap": "6px"},
                        children=[
                            _metric("Ensoleillement", f"{ens:.1f} h/j" if ens is not None else "N/A", "☀"),
                            _metric("Production", f"{prod:.0f} kWh" if prod is not None else "N/A", "⚡"),
                            _metric("Irradiance", f"{irr:.1f} kWh/m²" if irr is not None else "N/A", "🔆"),
                            _metric("Température moy.", f"{temp:.1f} °C" if temp is not None else "N/A", "🌡"),
                        ],
                    ),
                ],
            )
        ],
    )


# =========================
# Tiny K-Means (no deps)
# =========================
def _kmeans_2d(points: list[tuple[float, float]], k: int = 2, iters: int = 20):
    if not points or k <= 0:
        return [], []
    k = min(k, len(points))
    centroids = [list(points[i]) for i in range(k)]
    assign = [0] * len(points)

    for _ in range(iters):
        # assign
        for i, (x, y) in enumerate(points):
            best_j = 0
            best_d = None
            for j, (cx, cy) in enumerate(centroids):
                d = (x - cx) ** 2 + (y - cy) ** 2
                if best_d is None or d < best_d:
                    best_d = d
                    best_j = j
            assign[i] = best_j

        # update
        sums = [[0.0, 0.0, 0] for _ in range(k)]
        for (x, y), a in zip(points, assign):
            sums[a][0] += x
            sums[a][1] += y
            sums[a][2] += 1
        for j in range(k):
            if sums[j][2] > 0:
                centroids[j][0] = sums[j][0] / sums[j][2]
                centroids[j][1] = sums[j][1] / sums[j][2]
    return centroids, assign


# =========================
# Layout
# =========================
def render_optimisation(fig_opt, top_points_data, map_optimisation):
    """
    IMPORTANT:
    - top_points_data MUST be the FULL list of points (not just top5).
      In dashboard.py: pass opt_points_sorted.to_dict("records") here.
    """
    return html.Div(
        style={"padding": "10px 70px 0 70px", "width": "100%"},
        children=[
            # Stores
            dcc.Store(id="opt-all-points-data", data=top_points_data),
            dcc.Store(id="opt-minscore-store", data=60),
            dcc.Store(id="opt-top5-store", data=[]),
            dcc.Store(id="opt-map-top5-store", data=None),
            dcc.Store(id="opt-compare-store", data={"a": None, "b": None}),

            # polling for map->dash postMessage
            dcc.Interval(id="opt-map-poll", interval=700, n_intervals=0),

            # download
            dcc.Download(id="opt-download"),

            html.Div(
                style={"margin-bottom": "6px"},
                children=[
                    html.H1(
                        "Optimisation du placement des panneaux solaires",
                        style={"font-size": "34px", "margin": "0 0 6px 0", "line-height": "1.15"},
                    ),
                    html.P(
                        "Carte d'optimalité combinant ensoleillement, irradiance, production, précipitations et température "
                        "pour prioriser les emplacements les plus favorables.",
                        style={"font-size": "14px", "color": "#555", "max-width": "900px"},
                    ),
                ],
            ),

            html.Div(
                style={
                    "display": "grid",
                    "grid-template-columns": "2fr 1fr",
                    "gap": "20px",
                    "margin-bottom": "10px",
                    "align-items": "stretch",
                },
                children=[
                    # Map
                    dbc.Card(
                        style={
                            "border-radius": "18px",
                            "overflow": "hidden",
                            "box-shadow": "0 10px 24px rgba(0, 0, 0, 0.08)",
                            "border": "1px solid #e3ebff",
                            "height": "100%",
                            "min-height": "720px",
                        },
                        children=[
                            dbc.CardBody(
                                style={"padding": 0, "height": "100%", "display": "flex"},
                                children=[
                                    html.Iframe(
                                        id="map-optimisation-iframe",
                                        srcDoc=map_optimisation,
                                        style={
                                            "width": "100%",
                                            "height": "100%",
                                            "min-height": "720px",
                                            "display": "block",
                                            "border": "none",
                                        },
                                    )
                                ],
                            )
                        ],
                    ),

                    # Side panel
                    dbc.Card(
                        style={
                            "border-radius": "18px",
                            "box-shadow": "0 10px 24px rgba(0, 0, 0, 0.06)",
                            "border": "1px solid #e6ecff",
                            "height": "100%",
                            "min-height": "720px",
                        },
                        children=[
                            dbc.CardBody(
                                style={"display": "flex", "flex-direction": "column", "height": "100%"},
                                children=[
                                    html.Div(
                                        style={"display": "flex", "justify-content": "space-between", "align-items": "center", "gap": "10px"},
                                        children=[
                                            html.H4("Top 5 (dynamique)", style={"margin": "0", "font-size": "20px"}),
                                            html.Div(
                                                style={"display": "flex", "gap": "8px"},
                                                children=[
                                                    dbc.Button(
                                                        "🏆 Zoom #1",
                                                        id="opt-zoom-best-btn",
                                                        n_clicks=0,
                                                        size="sm",
                                                        color="primary",
                                                        style={"border-radius": "12px"},
                                                    ),
                                                    dbc.Button(
                                                        "📥 Export CSV",
                                                        id="opt-export-btn",
                                                        n_clicks=0,
                                                        size="sm",
                                                        color="light",
                                                        style={"border-radius": "12px"},
                                                    ),
                                                ],
                                            ),
                                        ],
                                    ),
                                    html.P(
                                        "Le filtre s'applique à la carte ET au Top 5 (synchro).",
                                        style={"font-size": "12px", "color": "#666", "margin-bottom": "8px"},
                                    ),

                                    html.Div(
                                        style={"display": "flex", "justify-content": "space-between", "align-items": "center"},
                                        children=[
                                            html.Span("Filtrer par score minimum", style={"font-size": "12px", "color": "#555"}),
                                            html.Span(id="opt-score-label", style={"font-size": "12px", "font-weight": "800", "color": "#005DFF"}),
                                        ],
                                    ),
                                    dcc.Slider(
                                        id="opt-score-slider",
                                        min=0,
                                        max=100,
                                        step=1,
                                        value=60,
                                        updatemode="drag",
                                        marks={0: "0%", 50: "50%", 70: "70%", 85: "85%", 100: "100%"},
                                        tooltip={"placement": "bottom", "always_visible": False},
                                    ),

                                    html.Div(style={"height": "10px"}),

                                    html.Div(
                                        style={"display": "flex", "gap": "10px", "align-items": "center", "margin-bottom": "8px"},
                                        children=[
                                            html.Div(_pill("🎯 Zoom", "rgba(0,93,255,0.08)", "#005DFF")),
                                            dcc.Dropdown(
                                                id="opt-focus-select",
                                                placeholder="Zoom sur un point (Top 5)…",
                                                clearable=True,
                                                style={"flex": "1", "font-size": "12px"},
                                                options=[],
                                                value=None,
                                            ),
                                        ],
                                    ),

                                    html.Div(
                                        id="opt-ml-insights",
                                        style={"margin-bottom": "10px"},
                                    ),

                                    html.Div(
                                        id="opt-compare-panel",
                                        style={"margin-bottom": "10px"},
                                    ),

                                    html.Div(
                                        id="opt-toast",
                                        style={"margin-bottom": "10px"},
                                    ),
                                    html.Div(id="opt-toast-copy", style={"display":"none"}),
                                    html.Div(id="opt-toast-zoom", style={"display":"none"}),


                                    html.Hr(style={"margin": "10px 0"}),

                                    html.Div(
                                        id="opt-top-points-list",
                                        style={"overflowY": "auto", "padding-right": "6px", "flex": "1", "min-height": "0"},
                                    ),

                                    # Bridges for iframe
                                    html.Div(id="opt-iframe-bridge", style={"display": "none"}),
                                    html.Div(id="opt-iframe-focus-bridge", style={"display": "none"}),
                                ],
                            )
                        ],
                    ),
                ],
            ),
        ],
    )


# =========================
# Callbacks
# =========================
def register_optimisation_callbacks(app):
    """Synchro slider <-> map, Top5 dynamique (visible), focus, export, copy, compare."""

    # 1) Store <-> slider sync
    @app.callback(
        Output("opt-minscore-store", "data"),
        Output("opt-score-label", "children"),
        Output("opt-score-slider", "value"),
        Input("opt-score-slider", "value"),
        Input("opt-minscore-store", "data"),
    )
    def _sync_slider_store(slider_v, store_v):
        trig = callback_context.triggered[0]["prop_id"].split(".")[0] if callback_context.triggered else ""
        if trig == "opt-score-slider":
            v = int(slider_v or 0)
        else:
            v = int(store_v or 0)
        v = max(0, min(100, v))
        return v, f"{v} %", v

    # 2) client-side: install map listener ONCE + update minscore-store from map
    app.clientside_callback(
        """
        function(n, current) {
          try {
            if (!window.__optMapListenerInstalled) {
              window.__optMapListenerInstalled = true;
              window.__optMinScoreFromMap = null;
              window.__optTop5FromMap = null;
              window.__optTop5MinScore = null;

              window.addEventListener("message", (event) => {
                const msg = event.data;
                if (!msg || !msg.type) return;

                if (msg.type === "MIN_SCORE_CHANGED") {
                  const v = Number(msg.value);
                  if (!isNaN(v)) window.__optMinScoreFromMap = Math.max(0, Math.min(100, v));
                }
                if (msg.type === "VISIBLE_TOP_CHANGED") {
                  window.__optTop5FromMap = msg.value;
                  window.__optTop5MinScore = Number(msg.minScore);
                }
              });
            }

            if (window.__optMinScoreFromMap === null || window.__optMinScoreFromMap === undefined) {
              return current;
            }
            const v = window.__optMinScoreFromMap;
            window.__optMinScoreFromMap = null;
            if (Number(current) === Number(v)) return current;
            return v;
          } catch (e) {
            return current;
          }
        }
        """,
        Output("opt-minscore-store", "data"),
        Input("opt-map-poll", "n_intervals"),
        State("opt-minscore-store", "data"),
    )

    # 2b) client-side: map -> top5 store (visible top5)
    app.clientside_callback(
        """
        function(n, current) {
          try {
            if (!window.__optMapListenerInstalled) return current;
            if (window.__optTop5FromMap === null || window.__optTop5FromMap === undefined) return current;

            const payload = { minScore: window.__optTop5MinScore, top5: window.__optTop5FromMap };
            window.__optTop5FromMap = null;
            return payload;
          } catch(e) {
            return current;
          }
        }
        """,
        Output("opt-map-top5-store", "data"),
        Input("opt-map-poll", "n_intervals"),
        State("opt-map-top5-store", "data"),
    )

    # 3) server-side: update list + ML + top5 store + focus dropdown
    @app.callback(
        Output("opt-top-points-list", "children"),
        Output("opt-ml-insights", "children"),
        Output("opt-top5-store", "data"),
        Output("opt-focus-select", "options"),
        Input("opt-minscore-store", "data"),
        State("opt-all-points-data", "data"),
        State("opt-map-top5-store", "data"),
    )
    def _update_list_and_ml(min_score, data, map_payload):
        if not data:
            empty = html.Div("Aucune donnée reçue (opt points).", style={"color": "#777", "font-size": "13px"})
            return empty, no_update, [], []

        points = data if isinstance(data, list) else data.get("points", [])
        if not isinstance(points, list):
            points = []

        enriched = []
        for p in points:
            if not isinstance(p, dict):
                continue
            sg = _compute_score_global(p)
            if sg is None:
                continue
            p2 = dict(p)
            p2["score_global"] = float(sg)
            enriched.append(p2)

        ms = float(min_score or 0)
        filtered = [p for p in enriched if float(p.get("score_global", 0)) >= ms]
        filtered.sort(key=lambda x: float(x.get("score_global", 0)), reverse=True)

        # Prefer the Top5 already filtered/sorted by the map (visible points) if it matches current threshold
        top5_from_map = None
        if isinstance(map_payload, dict) and isinstance(map_payload.get("top5"), list):
            try:
                mp_ms = map_payload.get("minScore")
                if mp_ms is None or int(float(mp_ms)) == int(float(ms)):
                    top5_from_map = [p for p in map_payload["top5"] if isinstance(p, dict)]
            except Exception:
                top5_from_map = None

        top5 = top5_from_map if top5_from_map is not None else filtered[:5]

        if not top5:
            list_children = html.Div(
                "Aucun point ne dépasse ce seuil. Baisse le score minimum.",
                style={"color": "#777", "font-size": "13px", "padding": "8px 2px"},
            )
        else:
            list_children = html.Div([_format_point_card(p, i) for i, p in enumerate(top5)])

        focus_opts = []
        for i, p in enumerate(top5):
            pid = p.get("idpoint") or p.get("id") or str(i + 1)
            sg = float(p.get("score_global", 0))
            focus_opts.append({"label": f"#{i+1}  ID {pid}  —  {sg:.1f}%", "value": str(pid)})

        # ML Insights: kmeans on best visible points
        pool = filtered[:80]
        coords = []
        scores = []
        for p in pool:
            lat = _safe_float(p.get("latitude"))
            lon = _safe_float(p.get("longitude"))
            sg = _safe_float(p.get("score_global"))
            if lat is None or lon is None or sg is None:
                continue
            coords.append((lat, lon))
            scores.append(sg)

        if len(coords) >= 10:
            centroids, assign = _kmeans_2d(coords, k=2, iters=25)
            clusters = [{"count": 0, "mean_score": 0.0} for _ in range(2)]
            for a, sc in zip(assign, scores[: len(assign)]):
                clusters[a]["count"] += 1
                clusters[a]["mean_score"] += sc
            for c in clusters:
                if c["count"] > 0:
                    c["mean_score"] /= c["count"]
            best_idx = max(range(2), key=lambda i: clusters[i]["mean_score"])
            best = clusters[best_idx]
            ml_children = html.Div(
                style={"display": "grid", "grid-template-columns": "1fr", "gap": "6px"},
                children=[
                    html.Div(
                        style={"display": "flex", "justify-content": "space-between", "align-items": "center"},
                        children=[
                            _pill("🤖 ML Insight", "rgba(46,204,113,0.12)", "#167E4B"),
                            html.Span(f"Seuil: {int(ms)}%", style={"font-size": "12px", "font-weight": "800", "color": "#005DFF"}),
                        ],
                    ),
                    html.Div(
                        style={"font-size": "12px", "color": "#444", "line-height": "1.4"},
                        children=[
                            html.Span("Hotspot suggéré (K-Means) : "),
                            html.B(f"{best['mean_score']:.1f}%"),
                            html.Span(f" (≈ {best['count']} points proches)"),
                        ],
                    ),
                    html.Div(
                        style={"font-size": "11px", "color": "#666"},
                        children="Astuce : augmente le seuil pour isoler les zones premium, puis utilise le hotspot ML sur la carte.",
                    ),
                ],
            )
        else:
            ml_children = html.Div(
                style={"display": "flex", "justify-content": "space-between", "align-items": "center"},
                children=[
                    _pill("🤖 ML Insight", "rgba(46,204,113,0.12)", "#167E4B"),
                    html.Span("Pas assez de points visibles pour le clustering.", style={"font-size": "11px", "color": "#777"}),
                ],
            )

        return list_children, ml_children, top5, focus_opts

    # 4) client-side: slider/store -> iframe map filter
    app.clientside_callback(
        """
        function(minScore) {
          try {
            const iframe = document.getElementById("optimisation-map");
            if (!iframe || !iframe.contentWindow) return "";
            iframe.contentWindow.postMessage({type: "SET_MIN_SCORE", value: minScore}, "*");
          } catch(e) {}
          return "";
        }
        """,
        Output("opt-iframe-bridge", "children"),
        Input("opt-minscore-store", "data"),
    )

    # 5) client-side: focus dropdown -> center map on selected point
    app.clientside_callback(
        """
        function(selectedId, top5) {
          try {
            if (!selectedId) return "";
            const iframe = document.getElementById("optimisation-map");
            if (!iframe || !iframe.contentWindow) return "";
            let lat = null, lon = null;
            if (Array.isArray(top5)) {
              for (const p of top5) {
                const pid = (p && (p.idpoint || p.id || p.ID));
                if (String(pid) === String(selectedId)) {
                  lat = p.latitude; lon = p.longitude;
                  break;
                }
              }
            }
            iframe.contentWindow.postMessage({type: "FOCUS_POINT", idpoint: selectedId, lat: lat, lon: lon, zoom: 12}, "*");
          } catch(e) {}
          return "";
        }
        """,
        Output("opt-iframe-focus-bridge", "children"),
        Input("opt-focus-select", "value"),
        State("opt-top5-store", "data"),
    )

    # 6) Zoom #1 button
    app.clientside_callback(
        """
        function(n, top5) {
          try {
            if (!n) return "";
            const iframe = document.getElementById("optimisation-map");
            if (!iframe || !iframe.contentWindow) return "";
            if (!Array.isArray(top5) || top5.length === 0) return "";
            const p = top5[0];
            const pid = p.idpoint || p.id || p.ID || "1";
            iframe.contentWindow.postMessage({type: "FOCUS_POINT", idpoint: String(pid), lat: p.latitude, lon: p.longitude, zoom: 12}, "*");
          } catch(e) {}
          return "";
        }
        """,
        Output("opt-toast-zoom", "children"),
        Input("opt-zoom-best-btn", "n_clicks"),
        State("opt-top5-store", "data"),
    )

    # 7) Export CSV Top5 (server)
    @app.callback(
        Output("opt-download", "data"),
        Input("opt-export-btn", "n_clicks"),
        State("opt-top5-store", "data"),
        prevent_initial_call=True,
    )
    def _export_csv(n, top5):
        if not n or not top5:
            return no_update
        rows = []
        for p in top5:
            if not isinstance(p, dict):
                continue
            rows.append(
                {
                    "idpoint": p.get("idpoint") or p.get("id") or p.get("ID"),
                    "score_global": p.get("score_global"),
                    "adresse": p.get("adresse"),
                    "latitude": p.get("latitude"),
                    "longitude": p.get("longitude"),
                    "ensoleillement": p.get("ensoleillement"),
                    "irradiance": p.get("irradiance"),
                    "production": p.get("production"),
                    "temperature": p.get("temperature"),
                }
            )
        if not rows:
            return no_update
        output = io.StringIO()
        # stable columns order
        cols = ["idpoint","score_global","adresse","latitude","longitude","ensoleillement","irradiance","production","temperature"]
        output.write(",".join(cols) + "\n")
        for r in rows:
            output.write(",".join([str(r.get(c, "")) for c in cols]) + "\n")
        return dcc.send_string(output.getvalue(), filename="top5_emplacements.csv")

    # 8) Copy lat/lon (client)
    # (handled below with dash_clientside.callback_context)

    # Better copy: use a second clientside callback that reads the triggered id (Dash provides it in dash_clientside.callback_context)
    app.clientside_callback(
        """
        function(nClicks, top5) {
          try {
            const ctx = dash_clientside.callback_context;
            if (!ctx || !ctx.triggered || ctx.triggered.length === 0) return "";
            const trig = ctx.triggered[0].prop_id;
            if (!trig) return "";
            const tid = JSON.parse(trig.split(".")[0]); // {type,index}
            const pid = String(tid.index);

            let lat=null, lon=null;
            if (Array.isArray(top5)) {
              for (const p of top5) {
                const idp = String(p.idpoint || p.id || p.ID);
                if (idp === pid) { lat=p.latitude; lon=p.longitude; break; }
              }
            }
            if (lat===null || lon===null) return "";

            const text = lat.toFixed ? (lat.toFixed(6)+", "+lon.toFixed(6)) : (String(lat)+", "+String(lon));
            if (navigator && navigator.clipboard && navigator.clipboard.writeText) {
              navigator.clipboard.writeText(text);
            }
            return "✅ Copié: " + text;
          } catch(e) {
            return "";
          }
        }
        """,
        Output("opt-toast-copy", "children"),
        Input({"type":"opt-copy-btn","index":ALL}, "n_clicks"),
        State("opt-top5-store","data"),
    )


    # Toast aggregator (avoid duplicate Outputs)
    @app.callback(
        Output("opt-toast", "children"),
        Input("opt-toast-copy", "children"),
        Input("opt-toast-zoom", "children"),
    )
    def _toast_agg(a, b):
        ctx = callback_context
        if not ctx.triggered:
            return no_update
        prop = ctx.triggered[0]["prop_id"].split(".")[0]
        if prop == "opt-toast-copy" and a:
            return a
        if prop == "opt-toast-zoom" and b:
            return b
        return b or a or no_update

    # 9) Compare selection (server)
    @app.callback(
        Output("opt-compare-store", "data"),
        Input({"type":"opt-compare-btn","index":ALL}, "n_clicks"),
        State("opt-compare-store","data"),
        prevent_initial_call=True,
    )
    def _update_compare_store(n_clicks_list, store):
        ctx = callback_context
        if not ctx.triggered:
            return no_update
        trig = ctx.triggered[0]["prop_id"].split(".")[0]
        try:
            tid = json.loads(trig) if trig.startswith('{') else None
        except Exception:
            tid = None
        if not isinstance(tid, dict):
            return no_update
        pid = str(tid.get("index"))
        s = store or {"a": None, "b": None}
        a, b = s.get("a"), s.get("b")
        # toggle logic
        if a == pid:
            a = None
        elif b == pid:
            b = None
        elif not a:
            a = pid
        elif not b:
            b = pid
        else:
            a, b = pid, None
        return {"a": a, "b": b}

    @app.callback(
        Output("opt-compare-panel","children"),
        Input("opt-compare-store","data"),
        State("opt-top5-store","data"),
    )
    def _render_compare(store, top5):
        a = (store or {}).get("a")
        b = (store or {}).get("b")
        if not a and not b:
            return html.Div(
                _pill("⚖️ Compare", "rgba(0,0,0,0.06)", "#333"),
                style={"font-size":"12px","color":"#666"}
            )

        def _get(pid):
            if not isinstance(top5, list):
                return None
            for p in top5:
                pid2 = str(p.get("idpoint") or p.get("id") or p.get("ID"))
                if pid2 == str(pid):
                    return p
            return None

        pa = _get(a) if a else None
        pb = _get(b) if b else None

        def _cell(p, title):
            if not p:
                return dbc.Card(dbc.CardBody("Sélectionne un point", style={"font-size":"12px","color":"#777"}), style={"border-radius":"14px"})
            return dbc.Card(
                dbc.CardBody(
                    [
                        html.Div(title, style={"font-weight":"900","font-size":"12px","margin-bottom":"6px"}),
                        html.Div(f"ID: {p.get('idpoint') or p.get('id') or p.get('ID')}", style={"font-size":"12px"}),
                        html.Div(f"Score: {float(p.get('score_global',0)):.1f}%", style={"font-size":"12px"}),
                        html.Div(f"Ens: {p.get('ensoleillement','')}", style={"font-size":"12px"}),
                        html.Div(f"Irr: {p.get('irradiance','')}", style={"font-size":"12px"}),
                        html.Div(f"Prod: {p.get('production','')}", style={"font-size":"12px"}),
                        html.Div(f"Temp: {p.get('temperature','')}", style={"font-size":"12px"}),
                    ]
                ),
                style={"border-radius":"14px","border":"1px solid #e6ecff","box-shadow":"0 6px 14px rgba(0,0,0,0.04)"},
            )

        return html.Div(
            [
                html.Div(_pill("⚖️ Compare (2 points)", "rgba(0,93,255,0.08)", "#005DFF")),
                html.Div(
                    style={"display":"grid","grid-template-columns":"1fr 1fr","gap":"10px","margin-top":"8px"},
                    children=[
                        _cell(pa, "A"),
                        _cell(pb, "B"),
                    ],
                ),
            ]
        )