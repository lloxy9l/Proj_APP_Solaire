import pandas as pd
import plotly.graph_objects as go

# Load the dataset
data = pd.read_csv('2026_solarx_consommation.csv')

# Check for any anomalies or outliers in the data
if data['consommation'].isnull().any():
    data['consommation'] = data['consommation'].fillna(0)  # Fill missing values with 0

# Pivot the data to prepare for heatmap visualization
heatmap_data = data.pivot_table(index='nom_commune', columns='annee', values='consommation', aggfunc='sum').fillna(0)

# Create the heatmap using Plotly
fig = go.Figure(data=go.Heatmap(
    z=heatmap_data.values,
    x=heatmap_data.columns,
    y=heatmap_data.index,
    text=heatmap_data.values,  # Add data values as text
    texttemplate="%{text:.2f}",  # Format text to show up to two decimal places
    colorscale='Viridis',
    colorbar=dict(title="Consumption"),
    zmin=0,  # Minimum value for the color scale
    zmax=7000
))

# Update layout for better visualization
fig.update_layout(
    title="Yearly Electricity Consumption by Commune",
    xaxis_title="Year",
    yaxis_title="Commune",
    xaxis=dict(tickmode="linear")
)

# Show the figure
fig.show()
