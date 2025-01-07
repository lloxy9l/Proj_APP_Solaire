from dash import Dash, html
import dash_leaflet as dl

# Créer l'application Dash
app = Dash(__name__)

# Ajouter la carte avec les tuiles OpenTopoMap
app.layout = html.Div([
    html.H1("Carte en Relief avec OpenTopoMap"),
    dl.Map([
        dl.TileLayer(
            url="https://tile.opentopomap.org/{z}/{x}/{y}.png",  # URL des tuiles
            attribution='&copy; <a href="https://opentopomap.org">OpenTopoMap</a>'
        )
    ],
        center=[46.2047, 6.14231],  # Latitude et longitude pour centrer la carte
        zoom=14,  # Niveau de zoom
        style={'width': '100%', 'height': '500px'}
    )
])

if __name__ == "__main__":
    app.run_server(debug=True)
