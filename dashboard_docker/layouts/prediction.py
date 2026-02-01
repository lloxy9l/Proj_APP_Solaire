from dash import html, dcc, Input, Output, State, no_update
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
from layouts.prediction_prophet import (
    create_prediction_table, 
    predict_for_all_points,
    predict_for_point,
    get_comparison_data,
    check_predictions_exist,
    get_all_points,
    clear_predictions,
    set_stop_flag
)
import time
import threading

# Variable globale pour suivre l'état des prédictions
prediction_status_global = {
    'running': False,
    'completed': False,
    'progress': 0,
    'total': 0,
    'current': 0,
    'message': ''
}

def render_prediction():
    """Rendu moderne de la page Prediction avec Prophet"""
    
    return html.Div(
        style={
            "padding": "30px",
            "minHeight": "100vh"
        },
        children=[
            # Container centré pour éviter la barre latérale
            html.Div(style={
                "maxWidth": "1400px",
                "margin": "0 auto",
                "paddingLeft": "20px",
                "paddingRight": "20px"
            }, children=[
            # Header avec design moderne
            html.Div([
                html.Div([
                    html.H1(
                        "Prédictions Météo IA",
                        style={
                            "color": "black",
                            "marginBottom": "10px",
                            "fontSize": "3rem",
                            "fontWeight": "700",
                            "textShadow": "2px 2px 4px rgba(0,0,0,0.2)"
                        }
                    ),
                    html.P(
                        "Intelligence Artificielle Prophet",
                        style={
                            "color": "black",
                            "fontSize": "1.1rem",
                            "marginBottom": "0"
                        }
                    ),
                ], style={
                    "textAlign": "center",
                    "marginBottom": "40px"
                }),
            ]),
            
            # Section Configuration - Card moderne
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-cog", style={
                            "fontSize": "24px",
                            "color": "#667eea",
                            "marginRight": "12px"
                        }),
                        html.H4("Configuration des prédictions", style={
                            "display": "inline-block",
                            "color": "#2d3748",
                            "fontWeight": "600",
                            "marginBottom": "0"
                        })
                    ], style={"marginBottom": "25px"}),
                    
                    dbc.Row([
                        # Période de prédiction
                        dbc.Col([
                            html.Label([
                                html.I(className="fas fa-calendar-alt", style={
                                    "marginRight": "8px",
                                    "color": "#667eea"
                                }),
                                "Période à prédire"
                            ], style={
                                "fontWeight": "600",
                                "color": "#4a5568",
                                "marginBottom": "10px",
                                "display": "block"
                            }),
                            dcc.Dropdown(
                                id="dropdown-period-prediction",
                                options=[
                                    {"label": "📆 1 jour", "value": "1_day"},
                                    {"label": "📅 1 semaine", "value": "1_week"},
                                    {"label": "📆 1 mois", "value": "1_month"},
                                    {"label": "📅 6 mois", "value": "6_months"},
                                    {"label": "📆 1 an", "value": "1_year"},
                                    {"label": "📅 5 ans", "value": "5_years"},
                                ],
                                value="1_year",
                                clearable=False,
                                style={
                                    "marginBottom": "15px",
                                    "borderRadius": "8px",
                                    "fontSize": "16px"
                                }
                            ),
                        ], lg=4, md=12),
                        
                        # Boutons d'action
                        dbc.Col([
                            html.Label([
                                html.I(className="fas fa-play-circle", style={
                                    "marginRight": "8px",
                                    "color": "#667eea"
                                }),
                                "Actions"
                            ], style={
                                "fontWeight": "600",
                                "color": "#4a5568",
                                "marginBottom": "10px",
                                "display": "block"
                            }),
                            html.Div([
                                dbc.Button([
                                    html.I(className="fas fa-rocket", style={"marginRight": "8px"}),
                                    "Lancer les prédictions"
                                ],
                                    id="btn-launch-predictions",
                                    color="primary",
                                    size="lg",
                                    style={
                                        "marginRight": "10px",
                                        "borderRadius": "10px",
                                        "fontWeight": "600",
                                        "boxShadow": "0 4px 6px rgba(0,0,0,0.1)",
                                        "transition": "all 0.3s"
                                    }
                                ),
                                dbc.Button([
                                    html.I(className="fas fa-stop-circle", style={"marginRight": "8px"}),
                                    "Arrêter"
                                ],
                                    id="btn-stop-predictions",
                                    color="warning",
                                    size="lg",
                                    style={
                                        "marginRight": "10px",
                                        "display": "none",
                                        "borderRadius": "10px",
                                        "fontWeight": "600",
                                        "boxShadow": "0 4px 6px rgba(0,0,0,0.1)"
                                    }
                                ),
                                dbc.Button([
                                    html.I(className="fas fa-trash-alt", style={"marginRight": "8px"}),
                                    "Effacer tout"
                                ],
                                    id="btn-clear-predictions",
                                    color="danger",
                                    size="lg",
                                    outline=True,
                                    style={
                                        "borderRadius": "10px",
                                        "fontWeight": "600",
                                        "boxShadow": "0 4px 6px rgba(0,0,0,0.1)"
                                    }
                                ),
                            ]),
                        ], lg=8, md=12),
                    ], className="mb-3"),
                    
                    # Status bar moderne
                    html.Div(
                        id="prediction-status",
                        style={
                            "marginTop": "25px",
                            "padding": "20px",
                            "background": "linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)",
                            "borderRadius": "12px",
                            "minHeight": "80px",
                            "boxShadow": "inset 0 2px 4px rgba(0,0,0,0.06)",
                            "display": "flex",
                            "alignItems": "center",
                            "justifyContent": "center"
                        }
                    ),
                    
                    # Barre de progression moderne
                    html.Div([
                        dbc.Progress(
                            id="prediction-progress",
                            value=0,
                            striped=True,
                            animated=True,
                            style={
                                "height": "30px",
                                "borderRadius": "15px",
                                "boxShadow": "0 2px 4px rgba(0,0,0,0.1)"
                            },
                            className="mb-0"
                        ),
                    ], style={
                        "marginTop": "15px",
                        "display": "none"
                    }, id="progress-container"),
                ]),
            ], style={
                "marginBottom": "30px",
                "borderRadius": "15px",
                "border": "none",
                "boxShadow": "0 10px 30px rgba(0,0,0,0.15)"
            }),
            
            # Section Visualisation - Card moderne
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-chart-line", style={
                            "fontSize": "24px",
                            "color": "#667eea",
                            "marginRight": "12px"
                        }),
                        html.H4("Visualisation des prédictions", style={
                            "display": "inline-block",
                            "color": "#2d3748",
                            "fontWeight": "600",
                            "marginBottom": "0"
                        })
                    ], style={"marginBottom": "25px"}),
                    
                    dbc.Row([
                        dbc.Col([
                            html.Label([
                                html.I(className="fas fa-map-marker-alt", style={
                                    "marginRight": "8px",
                                    "color": "#667eea"
                                }),
                                "Point GPS"
                            ], style={
                                "fontWeight": "600",
                                "color": "#4a5568",
                                "marginBottom": "10px",
                                "display": "block"
                            }),
                            # Dropdown amélioré avec recherche
                            dcc.Dropdown(
                                id="dropdown-point-prediction",
                                placeholder="🔍 Rechercher un point GPS...",
                                searchable=True,
                                style={
                                    "marginBottom": "15px",
                                    "fontSize": "15px"
                                },
                                # Style pour éviter le chevauchement
                                optionHeight=50,
                                maxHeight=300,
                            ),
                        ], lg=6, md=12),
                        
                        dbc.Col([
                            html.Label([
                                html.I(className="fas fa-thermometer-half", style={
                                    "marginRight": "8px",
                                    "color": "#667eea"
                                }),
                                "Variable à afficher"
                            ], style={
                                "fontWeight": "600",
                                "color": "#4a5568",
                                "marginBottom": "10px",
                                "display": "block"
                            }),
                            dcc.Dropdown(
                                id="dropdown-variable-prediction",
                                options=[
                                    {"label": "🌡️ Température (°C)", "value": "temperature"},
                                    {"label": "☀️ Ensoleillement (heures)", "value": "ensoleillement"},
                                    {"label": "🌧️ Précipitations (mm)", "value": "precipitation"},
                                    {"label": "⚡ Irradiance (W/m²)", "value": "irradiance"},
                                ],
                                value="temperature",
                                clearable=False,
                                style={
                                    "marginBottom": "15px",
                                    "fontSize": "15px"
                                }
                            ),
                        ], lg=6, md=12),
                    ]),
                    
                    # Graphique avec loading moderne
                    html.Div([
                        dcc.Loading(
                            id="loading-graph",
                            type="default",
                            color="#667eea",
                            children=[
                                dcc.Graph(
                                    id="graph-predictions",
                                    style={
                                        "height": "650px",
                                        "borderRadius": "12px",
                                        "overflow": "hidden"
                                    },
                                    config={
                                        'displayModeBar': True,
                                        'displaylogo': False,
                                        'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d']
                                    }
                                )
                            ]
                        ),
                    ], style={
                        "marginTop": "20px",
                        "borderRadius": "12px",
                        "overflow": "hidden",
                        "boxShadow": "0 4px 6px rgba(0,0,0,0.07)"
                    }),
                ]),
            ], style={
                "borderRadius": "15px",
                "border": "none",
                "boxShadow": "0 10px 30px rgba(0,0,0,0.15)"
            }),
            
            # Stores pour les données
            dcc.Store(id="store-predictions-ready", data=False),
            dcc.Store(id="store-prediction-trigger", data=0),
            dcc.Store(id="store-prediction-running", data=False),
            
            # Intervals
            dcc.Interval(
                id="interval-check-status",
                interval=1000,
                n_intervals=0,
                disabled=True
            ),
            
            dcc.Interval(
                id="interval-update-graph",
                interval=3000,
                n_intervals=0,
                disabled=True
            ),
            ]),  # Fin du container centré
        ],
    )


def register_prediction_callbacks(app):
    """Enregistre les callbacks pour la page de prédictions"""
    
    # Callback pour initialiser les dropdowns au chargement
    @app.callback(
        [Output("dropdown-point-prediction", "options"),
         Output("dropdown-point-prediction", "value"),
         Output("prediction-status", "children"),
         Output("graph-predictions", "figure")],
        Input("store-predictions-ready", "data"),
        prevent_initial_call=False
    )
    def init_page(dummy):
        """Initialize la page au chargement"""
        
        points = get_all_points()
        
        # Formatage amélioré des options avec emojis et meilleure lisibilité
        options = []
        for p in points:
            # Créer un label formaté avec l'ID et l'adresse
            label = f"📍 Point {p['idpoint']} - {p['adresse'][:50]}{'...' if len(p['adresse']) > 50 else ''}"
            options.append({
                "label": label,
                "value": p['idpoint']
            })
        
        # Vérifier si des prédictions existent
        has_predictions = check_predictions_exist()
        
        if has_predictions:
            status = html.Div([
                html.I(className="fas fa-check-circle", style={
                    "color": "#48bb78",
                    "fontSize": "28px",
                    "marginRight": "12px"
                }),
                html.Span([
                    "Des prédictions sont disponibles ! ",
                    html.Strong("Sélectionnez un point GPS pour visualiser.")
                ], style={
                    "color": "#2d3748",
                    "fontSize": "17px",
                    "fontWeight": "500"
                })
            ], style={
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "center"
            })
            first_point = options[0]['value'] if options else None
        else:
            status = html.Div([
                html.I(className="fas fa-info-circle", style={
                    "color": "#4299e1",
                    "fontSize": "28px",
                    "marginRight": "12px"
                }),
                html.Span([
                    "Aucune prédiction disponible. ",
                    html.Strong("Cliquez sur 'Lancer les prédictions' pour commencer.")
                ], style={
                    "color": "#2d3748",
                    "fontSize": "17px",
                    "fontWeight": "500"
                })
            ], style={
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "center"
            })
            first_point = None
        
        empty_fig = go.Figure()
        empty_fig.update_layout(
            template="plotly_white",
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            annotations=[
                dict(
                    text="Sélectionnez un point GPS pour afficher les prédictions",
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5,
                    showarrow=False,
                    font=dict(size=20, color="#a0aec0")
                )
            ],
            height=650,
            plot_bgcolor='#f7fafc'
        )
        
        return options, first_point, status, empty_fig
    
    # Callback pour lancer les prédictions
    @app.callback(
        [Output("prediction-status", "children", allow_duplicate=True),
         Output("interval-check-status", "disabled", allow_duplicate=True),
         Output("interval-update-graph", "disabled", allow_duplicate=True),
         Output("progress-container", "style", allow_duplicate=True),
         Output("btn-launch-predictions", "style", allow_duplicate=True),
         Output("btn-stop-predictions", "style", allow_duplicate=True),
         Output("store-prediction-running", "data", allow_duplicate=True)],
        Input("btn-launch-predictions", "n_clicks"),
        State("dropdown-period-prediction", "value"),
        prevent_initial_call=True
    )
    def launch_predictions(n_clicks, period):
        if not n_clicks:
            return no_update, no_update, no_update, no_update, no_update, no_update, no_update
        
        global prediction_status_global
        
        # Lancer dans un thread séparé
        def run_predictions():
            global prediction_status_global
            prediction_status_global['running'] = True
            prediction_status_global['completed'] = False
            
            def update_callback(idpoint, status, message):
                prediction_status_global['message'] = f"Point {idpoint}: {message}" if idpoint else message
            
            predict_for_all_points(period=period, callback=update_callback)
            
            prediction_status_global['running'] = False
            prediction_status_global['completed'] = True
        
        thread = threading.Thread(target=run_predictions, daemon=True)
        thread.start()
        
        status = html.Div([
            html.Div([
                html.I(className="fas fa-spinner fa-spin", style={
                    "color": "#667eea",
                    "fontSize": "28px",
                    "marginRight": "12px"
                }),
                html.Span(
                    "Génération des prédictions en cours...",
                    style={
                        "color": "#2d3748",
                        "fontSize": "17px",
                        "fontWeight": "500"
                    }
                )
            ], style={
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "center"
            })
        ])
        
        progress_style = {"marginTop": "15px", "display": "block"}
        launch_btn_style = {"marginRight": "10px", "display": "none", "borderRadius": "10px", "fontWeight": "600"}
        stop_btn_style = {"marginRight": "10px", "display": "inline-block", "borderRadius": "10px", "fontWeight": "600"}
        
        return status, False, False, progress_style, launch_btn_style, stop_btn_style, True
    
    # Callback pour surveiller l'état
    @app.callback(
        [Output("prediction-status", "children", allow_duplicate=True),
         Output("prediction-progress", "value", allow_duplicate=True)],
        Input("interval-check-status", "n_intervals"),
        State("store-prediction-running", "data"),
        prevent_initial_call=True
    )
    def check_prediction_status(n_intervals, is_running):
        global prediction_status_global
        
        if not is_running:
            return no_update, no_update
        
        message = prediction_status_global.get('message', 'En cours...')
        progress = min(prediction_status_global.get('progress', 0), 100)
        
        if prediction_status_global.get('completed', False):
            status = html.Div([
                html.I(className="fas fa-check-circle", style={
                    "color": "#48bb78",
                    "fontSize": "28px",
                    "marginRight": "12px"
                }),
                html.Span(
                    "✅ Prédictions terminées avec succès !",
                    style={
                        "color": "#2d3748",
                        "fontSize": "17px",
                        "fontWeight": "500"
                    }
                )
            ], style={
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "center"
            })
            return status, 100
        
        status = html.Div([
            html.I(className="fas fa-spinner fa-spin", style={
                "color": "#667eea",
                "fontSize": "28px",
                "marginRight": "12px"
            }),
            html.Span(
                message,
                style={
                    "color": "#2d3748",
                    "fontSize": "17px",
                    "fontWeight": "500"
                }
            )
        ], style={
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "center"
        })
        
        return status, progress
    
    # Callback pour arrêter les prédictions
    @app.callback(
        [Output("prediction-status", "children", allow_duplicate=True),
         Output("interval-check-status", "disabled", allow_duplicate=True),
         Output("interval-update-graph", "disabled", allow_duplicate=True),
         Output("progress-container", "style", allow_duplicate=True),
         Output("btn-launch-predictions", "style", allow_duplicate=True),
         Output("btn-stop-predictions", "style", allow_duplicate=True),
         Output("store-prediction-running", "data", allow_duplicate=True)],
        Input("btn-stop-predictions", "n_clicks"),
        prevent_initial_call=True
    )
    def stop_predictions(n_clicks):
        if not n_clicks:
            return no_update, no_update, no_update, no_update, no_update, no_update, no_update
        
        global prediction_status_global
        set_stop_flag(True)
        prediction_status_global['running'] = False
        prediction_status_global['completed'] = True
        
        status = html.Div([
            html.I(className="fas fa-stop-circle", style={
                "color": "#ed8936",
                "fontSize": "28px",
                "marginRight": "12px"
            }),
            html.Span(
                "⏸️ Arrêté par l'utilisateur.",
                style={
                    "color": "#2d3748",
                    "fontSize": "17px",
                    "fontWeight": "500"
                }
            )
        ], style={
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "center"
        })
        
        progress_style = {"marginTop": "15px", "display": "none"}
        launch_btn_style = {"marginRight": "10px", "display": "inline-block", "borderRadius": "10px", "fontWeight": "600"}
        stop_btn_style = {"marginRight": "10px", "display": "none", "borderRadius": "10px", "fontWeight": "600"}
        
        return status, True, True, progress_style, launch_btn_style, stop_btn_style, False
    
    # Callback pour effacer les prédictions
    @app.callback(
        Output("prediction-status", "children", allow_duplicate=True),
        Input("btn-clear-predictions", "n_clicks"),
        prevent_initial_call=True
    )
    def clear_all_predictions(n_clicks):
        if not n_clicks:
            return no_update
        
        clear_predictions()
        
        status = html.Div([
            html.I(className="fas fa-trash-alt", style={
                "color": "#f56565",
                "fontSize": "28px",
                "marginRight": "12px"
            }),
            html.Span(
                "🗑️ Toutes les prédictions ont été effacées.",
                style={
                    "color": "#2d3748",
                    "fontSize": "17px",
                    "fontWeight": "500"
                }
            )
        ], style={
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "center"
        })
        
        return status
    
    # Callback pour mettre à jour le graphique
    @app.callback(
        [Output("graph-predictions", "figure", allow_duplicate=True),
         Output("prediction-progress", "value", allow_duplicate=True)],
        [Input("dropdown-point-prediction", "value"),
         Input("dropdown-variable-prediction", "value"),
         Input("dropdown-period-prediction", "value"),
         Input("interval-update-graph", "n_intervals")],
        prevent_initial_call=True
    )
    def update_prediction_graph(idpoint, variable, period, n_intervals):
        if not idpoint or not variable:
            return go.Figure(), 0
        
        try:
            df = get_comparison_data(idpoint, variable)
            
            if df.empty:
                return go.Figure(), 0
            
            fig = create_prediction_graph(df, idpoint, variable, period)
            
            has_predictions = len(df[df['type'] == 'Prédiction']) > 0
            progress = 100 if has_predictions else 50
            
            return fig, progress
            
        except Exception as e:
            print(f"Erreur update_prediction_graph: {e}")
            return go.Figure(), 0


def create_prediction_graph(df, idpoint, variable, period=None):
    """Crée le graphique moderne de comparaison historique vs prédictions"""
    
    fig = go.Figure()
    
    labels = {
        'temperature': '🌡️ Température (°C)',
        'ensoleillement': '☀️ Ensoleillement (heures)',
        'precipitation': '🌧️ Précipitations (mm)',
        'irradiance': '⚡ Irradiance (W/m²)'
    }
    
    # Couleurs modernes
    colors = {
        'historique': '#667eea',
        'prediction': '#f093fb'
    }
    
    df['value'] = pd.to_numeric(df['value'], errors='coerce')
    df['date'] = pd.to_datetime(df['date'])
    df = df.dropna(subset=['value'])
    
    df_hist = df[df['type'] == 'Historique'].copy()
    df_pred = df[df['type'] == 'Prédiction'].copy()
    
    if period is not None and not df_pred.empty and not df_hist.empty:
        last_hist_date = df_hist['date'].max()
        
        from datetime import timedelta
        period_days = {
            '1_day': 1,
            '1_week': 7,
            '1_month': 30,
            '6_months': 180,
            '1_year': 365,
            '5_years': 1825
        }
        
        days = period_days.get(period, 365)
        end_date = last_hist_date + timedelta(days=days)
        df_pred = df_pred[df_pred['date'] <= end_date]
    
    # Historique avec style moderne
    if not df_hist.empty:
        fig.add_trace(go.Scatter(
            x=df_hist['date'],
            y=df_hist['value'],
            mode='lines',
            name='📊 Données Historiques',
            line=dict(color=colors['historique'], width=3),
            fill='tozeroy',
            fillcolor=f'rgba(102, 126, 234, 0.1)',
            hovertemplate='<b>%{x|%d/%m/%Y}</b><br>Valeur: <b>%{y:.2f}</b><extra></extra>'
        ))
    
    # Prédictions avec style moderne
    if not df_pred.empty:
        fig.add_trace(go.Scatter(
            x=df_pred['date'],
            y=df_pred['value'],
            mode='lines',
            name='🔮 Prédictions IA',
            line=dict(color=colors['prediction'], width=3.5, dash='solid'),
            fill='tozeroy',
            fillcolor=f'rgba(240, 147, 251, 0.15)',
            hovertemplate='<b>%{x|%d/%m/%Y}</b><br>Prédiction: <b>%{y:.2f}</b><extra></extra>'
        ))
    
    # Configuration des axes
    all_values = pd.concat([df_hist['value'], df_pred['value']]).dropna()
    
    if not all_values.empty and len(all_values) > 0:
        y_max = float(all_values.max())
        y_min = float(all_values.min())
        y_range = max(abs(y_max), abs(y_min)) * 1.15
        
        yaxis_config = dict(
            showgrid=True,
            gridcolor='rgba(200, 200, 200, 0.2)',
            zeroline=True,
            zerolinewidth=2,
            zerolinecolor='rgba(100, 100, 100, 0.3)',
            range=[-y_range, y_range]
        )
    else:
        yaxis_config = dict(
            showgrid=True,
            gridcolor='rgba(200, 200, 200, 0.2)',
            zeroline=True,
            zerolinewidth=2,
            zerolinecolor='rgba(100, 100, 100, 0.3)'
        )
    
    period_labels = {
        '1_day': '1 jour',
        '1_week': '1 semaine',
        '1_month': '1 mois',
        '6_months': '6 mois',
        '1_year': '1 an',
        '5_years': '5 ans'
    }
    
    period_text = period_labels.get(period, 'Toutes') if period else 'Toutes'
    
    # Layout moderne
    fig.update_layout(
        title={
            'text': f"{labels.get(variable, variable)} - Point GPS {idpoint}<br><sub style='font-size:14px; color:#718096;'>Historique vs Prédictions IA ({period_text})</sub>",
            'font': {'size': 24, 'color': '#2d3748', 'family': 'Arial, sans-serif'},
            'x': 0.5,
            'xanchor': 'center',
            'y': 0.95,
            'yanchor': 'top'
        },
        xaxis_title=dict(
            text="📅 Date",
            font=dict(size=14, color='#4a5568', family='Arial, sans-serif')
        ),
        yaxis_title=dict(
            text=labels.get(variable, variable),
            font=dict(size=14, color='#4a5568', family='Arial, sans-serif')
        ),
        template="plotly_white",
        hovermode="x unified",
        legend=dict(
            x=0.02,
            y=0.98,
            bgcolor='rgba(255, 255, 255, 0.95)',
            bordercolor='#667eea',
            borderwidth=2,
            font=dict(size=13, family='Arial, sans-serif'),
            orientation='v'
        ),
        height=650,
        plot_bgcolor='#fafafa',
        paper_bgcolor='white',
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(200, 200, 200, 0.2)',
            tickformat='%d/%m/%Y',
            tickfont=dict(size=11, color='#4a5568')
        ),
        yaxis=yaxis_config,
        margin=dict(l=60, r=40, t=120, b=60),
        font=dict(family='Arial, sans-serif')
    )
    
    return fig