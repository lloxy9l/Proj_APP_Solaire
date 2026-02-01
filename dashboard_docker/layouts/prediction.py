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

# 🔧 FIX: Variable globale pour suivre l'état des prédictions
prediction_status_global = {
    'running': False,
    'completed': False,
    'progress': 0,
    'total': 0,
    'current': 0,
    'message': ''
}

def render_prediction():
    """Rendu de la page Prediction avec Prophet"""
    
    return html.Div(
        style={"padding": "20px", "height": "100%"},
        children=[
            # Header
            html.H1(
                "🔮 Prédictions Météo avec Intelligence Artificielle",
                style={
                    "textAlign": "center",
                    "color": "#005dff",
                    "marginBottom": "10px"
                }
            ),
            html.P(
                "Prédictions basées sur Prophet (Facebook) avec saisonnalité complète",
                style={"textAlign": "center", "color": "#666", "marginBottom": "30px"}
            ),
            
            # Section contrôle
            dbc.Card(
                dbc.CardBody([
                    html.H4("Configuration des prédictions", className="card-title"),
                    
                    dbc.Row([
                        # Période de prédiction
                        dbc.Col([
                            html.Label("Période à prédire:", style={"fontWeight": "bold"}),
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
                                style={"marginBottom": "15px"}
                            ),
                        ], width=4),
                        
                        # Boutons d'action
                        dbc.Col([
                            html.Label("Actions:", style={"fontWeight": "bold"}),
                            html.Div([
                                dbc.Button(
                                    "Lancer les prédictions",
                                    id="btn-launch-predictions",
                                    color="primary",
                                    size="lg",
                                    style={"marginRight": "10px"}
                                ),
                                dbc.Button(
                                    "⏸️ Stop",
                                    id="btn-stop-predictions",
                                    color="warning",
                                    size="lg",
                                    style={"marginRight": "10px", "display": "none"}
                                ),
                                dbc.Button(
                                    "Effacer",
                                    id="btn-clear-predictions",
                                    color="danger",
                                    size="lg",
                                    outline=True
                                ),
                            ]),
                        ], width=8),
                    ]),
                    
                    # Status bar
                    html.Div(
                        id="prediction-status",
                        style={
                            "marginTop": "20px",
                            "padding": "15px",
                            "backgroundColor": "#f8f9fa",
                            "borderRadius": "8px",
                            "minHeight": "60px"
                        }
                    ),
                    
                    # Barre de progression
                    dbc.Progress(
                        id="prediction-progress",
                        value=0,
                        striped=True,
                        animated=True,
                        style={"marginTop": "10px", "height": "25px", "display": "none"}
                    ),
                ]),
                style={"marginBottom": "30px"}
            ),
            
            # Section visualisation
            dbc.Card(
                dbc.CardBody([
                    html.H4("Visualisation des prédictions", className="card-title"),
                    
                    dbc.Row([
                        dbc.Col([
                            html.Label(" Sélectionner un point GPS:", style={"fontWeight": "bold"}),
                            dcc.Dropdown(
                                id="dropdown-point-prediction",
                                placeholder="Choisir un point GPS...",
                                style={"marginBottom": "15px"}
                            ),
                        ], width=6),
                        dbc.Col([
                            html.Label("Variable à afficher:", style={"fontWeight": "bold"}),
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
                                style={"marginBottom": "15px"}
                            ),
                        ], width=6),
                    ]),
                    
                    # Graphique
                    dcc.Loading(
                        id="loading-graph",
                        type="default",
                        children=[
                            dcc.Graph(
                                id="graph-predictions",
                                style={"height": "600px"}
                            )
                        ]
                    ),
                ]),
            ),
            
            # Stores pour les données
            dcc.Store(id="store-predictions-ready", data=False),
            dcc.Store(id="store-prediction-trigger", data=0),
            dcc.Store(id="store-prediction-running", data=False),
            
            # 🔧 FIX: Interval pour surveiller l'état des prédictions
            dcc.Interval(
                id="interval-check-status",
                interval=1000,  # Vérifier toutes les secondes
                n_intervals=0,
                disabled=True
            ),
            
            # Interval pour mise à jour graphique
            dcc.Interval(
                id="interval-update-graph",
                interval=3000,
                n_intervals=0,
                disabled=True
            ),
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
        options = [{"label": f" Point {p['idpoint']} - {p['adresse']}", "value": p['idpoint']} for p in points]
        default_point = points[0]['idpoint'] if points else None
        
        has_predictions = check_predictions_exist()
        
        if has_predictions:
            status = html.Div([
                html.I(className="fas fa-check-circle", style={"color": "green", "fontSize": "24px"}),
                html.Span(
                    " Des prédictions sont disponibles. Sélectionnez un point pour les visualiser.",
                    style={"marginLeft": "10px", "color": "green", "fontSize": "16px"}
                )
            ])
        else:
            status = html.Div([
                html.I(className="fas fa-info-circle", style={"color": "#005dff", "fontSize": "24px"}),
                html.Span(
                    " Aucune prédiction disponible. Lancez une prédiction pour commencer.",
                    style={"marginLeft": "10px", "color": "#666", "fontSize": "16px"}
                )
            ])
        
        fig = go.Figure()
        fig.update_layout(
            title="Sélectionnez un point GPS pour voir les prédictions",
            template="plotly_white",
            height=600
        )
        
        return options, default_point, status, fig
    
    # Callback principal pour lancer les prédictions
    @app.callback(
        [Output("prediction-status", "children", allow_duplicate=True),
         Output("interval-check-status", "disabled"),
         Output("interval-update-graph", "disabled"),
         Output("prediction-progress", "style"),
         Output("btn-launch-predictions", "style"),
         Output("btn-stop-predictions", "style"),
         Output("store-prediction-running", "data")],
        Input("btn-launch-predictions", "n_clicks"),
        State("dropdown-period-prediction", "value"),
        prevent_initial_call=True
    )
    def launch_predictions(n_clicks, period):
        if not n_clicks:
            return no_update, no_update, no_update, no_update, no_update, no_update, no_update
        
        global prediction_status_global
        
        # Réinitialiser le statut
        prediction_status_global = {
            'running': True,
            'completed': False,
            'progress': 0,
            'total': len(get_all_points()),
            'current': 0,
            'message': 'Démarrage des prédictions...'
        }
        
        # Callback pour mise à jour du statut
        def status_callback(idpoint, status_type, message):
            prediction_status_global['message'] = message
            if status_type == "processing":
                prediction_status_global['current'] = idpoint
            elif status_type == "success":
                prediction_status_global['progress'] = prediction_status_global['current']
        
        # Lancer dans un thread
        def run_predictions():
            try:
                predict_for_all_points(period, status_callback)
            finally:
                # ✅ FIX: Marquer comme terminé quand le thread se termine
                prediction_status_global['running'] = False
                prediction_status_global['completed'] = True
                print("✅ Thread de prédictions terminé")
        
        thread = threading.Thread(target=run_predictions, daemon=True)
        thread.start()
        
        status = html.Div([
            html.I(className="fas fa-spinner fa-spin", style={"color": "#005dff", "fontSize": "24px"}),
            html.Span(
                f" 🚀 Lancement des prédictions pour {prediction_status_global['total']} points...",
                style={"marginLeft": "10px", "color": "#005dff", "fontSize": "16px"}
            )
        ])
        
        progress_style = {"marginTop": "10px", "height": "25px", "display": "block"}
        launch_btn_style = {"marginRight": "10px", "display": "none"}
        stop_btn_style = {"marginRight": "10px", "display": "inline-block"}
        
        # ✅ Activer les deux intervals
        return status, False, False, progress_style, launch_btn_style, stop_btn_style, True
    
    # ✅ FIX: Callback pour surveiller l'état et DÉSACTIVER les intervals quand terminé
    @app.callback(
        [Output("prediction-status", "children", allow_duplicate=True),
         Output("prediction-progress", "value"),
         Output("prediction-progress", "label"),
         Output("interval-check-status", "disabled", allow_duplicate=True),
         Output("interval-update-graph", "disabled", allow_duplicate=True),
         Output("btn-launch-predictions", "style", allow_duplicate=True),
         Output("btn-stop-predictions", "style", allow_duplicate=True),
         Output("store-prediction-running", "data", allow_duplicate=True)],
        Input("interval-check-status", "n_intervals"),
        State("store-prediction-running", "data"),
        prevent_initial_call=True
    )
    def check_prediction_status(n_intervals, is_running):
        global prediction_status_global
        
        # Si les prédictions ne tournent pas, ne rien faire
        if not is_running or not prediction_status_global['running']:
            # ✅ FIX: Si terminé, désactiver les intervals
            if prediction_status_global.get('completed', False):
                status = html.Div([
                    html.I(className="fas fa-check-circle", style={"color": "green", "fontSize": "24px"}),
                    html.Span(
                        f" ✅ Prédictions terminées ! {prediction_status_global['progress']}/{prediction_status_global['total']} points traités.",
                        style={"marginLeft": "10px", "color": "green", "fontSize": "16px"}
                    )
                ])
                
                launch_btn_style = {"marginRight": "10px", "display": "inline-block"}
                stop_btn_style = {"marginRight": "10px", "display": "none"}
                
                # ✅ DÉSACTIVER LES DEUX INTERVALS
                return status, 100, "100%", True, True, launch_btn_style, stop_btn_style, False
            
            return no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update
        
        # Calculer la progression
        total = prediction_status_global['total']
        current = prediction_status_global['progress']
        progress = int((current / total) * 100) if total > 0 else 0
        
        # Créer le message de statut
        status = html.Div([
            html.I(className="fas fa-spinner fa-spin", style={"color": "#005dff", "fontSize": "24px"}),
            html.Span(
                f" {prediction_status_global['message']} ({current}/{total})",
                style={"marginLeft": "10px", "color": "#005dff", "fontSize": "16px"}
            )
        ])
        
        label = f"{progress}%"
        
        # Les intervals restent activés (False)
        return status, progress, label, False, False, no_update, no_update, True
    
    # Callback pour arrêter les prédictions
    @app.callback(
        [Output("prediction-status", "children", allow_duplicate=True),
         Output("interval-check-status", "disabled", allow_duplicate=True),
         Output("interval-update-graph", "disabled", allow_duplicate=True),
         Output("prediction-progress", "style", allow_duplicate=True),
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
        prediction_status_global['completed'] = True  # ✅ Marquer comme terminé
        
        status = html.Div([
            html.I(className="fas fa-stop-circle", style={"color": "orange", "fontSize": "24px"}),
            html.Span(
                " ⏸️ Arrêté par l'utilisateur.",
                style={"marginLeft": "10px", "color": "orange", "fontSize": "16px"}
            )
        ])
        
        progress_style = {"marginTop": "10px", "height": "25px", "display": "none"}
        launch_btn_style = {"marginRight": "10px", "display": "inline-block"}
        stop_btn_style = {"marginRight": "10px", "display": "none"}
        
        # ✅ DÉSACTIVER LES DEUX INTERVALS
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
            html.I(className="fas fa-trash", style={"color": "red", "fontSize": "24px"}),
            html.Span(
                " Toutes les prédictions ont été effacées.",
                style={"marginLeft": "10px", "color": "red", "fontSize": "16px"}
            )
        ])
        
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
    """Crée le graphique de comparaison historique vs prédictions"""
    
    fig = go.Figure()
    
    labels = {
        'temperature': '🌡️ Température (°C)',
        'ensoleillement': '☀️ Ensoleillement (heures)',
        'precipitation': '🌧️ Précipitations (mm)',
        'irradiance': '⚡ Irradiance (W/m²)'
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
    
    print(f"📊 Point {idpoint}, Variable {variable}: Hist={len(df_hist)}, Pred={len(df_pred)}")
    
    if not df_hist.empty:
        fig.add_trace(go.Scatter(
            x=df_hist['date'],
            y=df_hist['value'],
            mode='lines',
            name='📊 Historique (2019-2024)',
            line=dict(color='#005dff', width=2.5),
            hovertemplate='<b>Date:</b> %{x|%Y-%m-%d}<br><b>Valeur:</b> %{y:.2f}<extra></extra>'
        ))
    
    if not df_pred.empty:
        fig.add_trace(go.Scatter(
            x=df_pred['date'],
            y=df_pred['value'],
            mode='lines',
            name='🔮 Prédictions AI',
            line=dict(color='#ff4757', width=3, dash='solid'),
            hovertemplate='<b>Date:</b> %{x|%Y-%m-%d}<br><b>Prédiction:</b> %{y:.2f}<extra></extra>'
        ))
    
    all_values = pd.concat([df_hist['value'], df_pred['value']]).dropna()
    
    if not all_values.empty and len(all_values) > 0:
        y_max = float(all_values.max())
        y_min = float(all_values.min())
        y_range = max(abs(y_max), abs(y_min)) * 1.1
        
        yaxis_config = dict(
            showgrid=True,
            gridcolor='#e0e0e0',
            zeroline=True,
            zerolinewidth=2,
            zerolinecolor='#2c3e50',
            range=[-y_range, y_range]
        )
    else:
        yaxis_config = dict(
            showgrid=True,
            gridcolor='#e0e0e0',
            zeroline=True,
            zerolinewidth=2,
            zerolinecolor='#2c3e50'
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
    
    fig.update_layout(
        title={
            'text': f"{labels.get(variable, variable)} - Point GPS {idpoint}<br><sub>Historique vs Prédictions ({period_text}) avec saisonnalité</sub>",
            'font': {'size': 22, 'color': '#2c3e50'},
            'x': 0.5,
            'xanchor': 'center'
        },
        xaxis_title="📅 Date",
        yaxis_title=labels.get(variable, variable),
        template="plotly_white",
        hovermode="x unified",
        legend=dict(
            x=0.01, 
            y=0.99,
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='#005dff',
            borderwidth=2
        ),
        height=600,
        plot_bgcolor='#f8f9fa',
        xaxis=dict(
            showgrid=True,
            gridcolor='#e0e0e0',
            tickformat='%Y-%m-%d'
        ),
        yaxis=yaxis_config,
        annotations=[
            dict(
                text="Prophet AI avec saisonnalité complète",
                xref="paper", yref="paper",
                x=0.5, y=-0.15,
                showarrow=False,
                font=dict(size=12, color='#7f8c8d')
            )
        ]
    )
    
    return fig