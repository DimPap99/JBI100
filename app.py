import dash
from dash import dcc, html
import pandas as pd
from dash.dependencies import Input, Output, State
import plotly.express as px
from datetime import datetime as dt

# Initialize the Dash app
app = dash.Dash(__name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}])
app.title = "Shark Incidents in Australia"
server = app.server

# ---------------------------------
# Load and preprocess your dataset
# ---------------------------------
df = pd.read_csv("shark.csv")  # <-- Adjust path as needed
df = df.dropna(subset=["Latitude", "Longitude"])
df["Date"] = pd.to_datetime(
    df["Incident.year"].astype(str) + "-" + df["Incident.month"].astype(str),
    errors="coerce"
)

# Build the list of species for the dropdown
species_options = [
    {"label": species, "value": species}
    for species in df["Shark.common.name"].dropna().unique()
]

df["Latitude"] = pd.to_numeric(df["Latitude"], errors="coerce")
df["Longitude"] = pd.to_numeric(df["Longitude"], errors="coerce")

# -----------------------
# App Layout
# -----------------------
app.layout = html.Div([
    html.Div(
        id="background-container",  # Add an ID to the background container
        children=[
            html.Div(
                className="row",
                children=[
                    # Left column with controls
                    html.Div(
                        className="four columns div-user-controls",
                        children=[
                            html.H2("DASH - SHARK INCIDENT DATA"),
                            html.P("Select a date (month/day) to filter incidents."),
                            dcc.DatePickerSingle(
                                id="date-picker",
                                min_date_allowed=dt(1791, 1, 1),
                                max_date_allowed=dt(2022, 12, 31),
                                initial_visible_month=dt(2022, 1, 1),
                                date=dt(2022, 1, 1).date(),
                                display_format="MMMM D, YYYY",
                            ),
                            html.P("Filter by shark species:"),
                            dcc.Dropdown(
                                id="species-dropdown",
                                options=species_options,
                                placeholder="Select a Shark Species",
                            ),
                        ],
                    ),
                    # Right column with the map
                    html.Div(
                        className="eight columns div-for-charts bg-grey",
                        children=[
                            dcc.Graph(id="map-graph", config={"scrollZoom": True}),
                        ],
                    ),
                ],
            ),
        ],
    ),
    
    # Store for incidents
    dcc.Store(id="selected-incidents-store", data={"rows": [], "current_index": 0}),

    # Modal
    html.Div(
        id="info-modal",
        style={
            "display": "none",
            "position": "fixed",
            "top": "20%",
            "left": "30%",
            "width": "40%",
            "height": "40%",
            "backgroundColor": "white",
            "boxShadow": "0px 0px 10px rgba(0, 0, 0, 0.5)",
            "zIndex": 1000,
            "padding": "20px",
            "borderRadius": "10px",
        },
        children=[
            html.Button("Close", id="close-modal", style={"float": "right", "margin": "10px"}),
            html.Div([
                html.Button("Previous", id="prev-incident", n_clicks=0, style={"marginRight": "10px"}),
                html.Button("Next", id="next-incident", n_clicks=0)
            ], style={"marginBottom": "10px"}),
            html.Div(id="modal-incident-content"),
        ],
    ),
])

# CSS Styles (Place in `assets/style.css` file)
"""
#background-container {
    transition: filter 0.3s ease;
}
#background-container.blurred {
    filter: blur(5px);
}
"""

# Callback to update the map
@app.callback(
    Output("map-graph", "figure"),
    Input("date-picker", "date"),
    Input("species-dropdown", "value"),
    Input("map-graph", "clickData"),
)
def update_graph(datePicked, selectedSpecies, clickData):
    date_picked = pd.to_datetime(datePicked)
    if pd.isnull(date_picked):
        filtered_df = df.copy()
    else:
        filtered_df = df[
            (df["Date"].dt.month == date_picked.month) &
            (df["Date"].dt.day == date_picked.day)
        ]

    if selectedSpecies:
        filtered_df = filtered_df[filtered_df["Shark.common.name"] == selectedSpecies]

    bubble_data = filtered_df.groupby(
        ["Latitude", "Longitude"]
    ).size().reset_index(name="Incident Count")

    zoom_level = 4
    center = {"lat": -25.0, "lon": 133.0}

    if clickData:
        clicked_point = clickData["points"][0]
        center = {"lat": float(clicked_point["lat"]), "lon": float(clicked_point["lon"])}
        zoom_level = 8

    fig = px.scatter_mapbox(
        bubble_data,
        lat="Latitude",
        lon="Longitude",
        size="Incident Count",
        hover_name="Incident Count",
        color_discrete_sequence=["#636EFA"],
        zoom=zoom_level,
        center=center,
        mapbox_style="open-street-map",
    )
    fig.update_traces(marker=dict(opacity=0.5))
    fig.update_layout(
        title="Shark Incidents Density",
        margin={"r": 0, "t": 0, "l": 0, "b": 0}
    )
    return fig

# Callback to toggle modal and blur effect
@app.callback(
    Output("background-container", "className"),
    Output("info-modal", "style"),
    [
        Input("map-graph", "clickData"),
        Input("close-modal", "n_clicks"),
    ],
    prevent_initial_call=True,
)
def toggle_modal_and_blur(clickData, close_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        return "", {"display": "none"}

    triggered_input = ctx.triggered[0]["prop_id"]
    if "close-modal" in triggered_input:
        return "", {"display": "none"}
    elif "map-graph.clickData" in triggered_input and clickData:
        return "blurred", {
            "display": "block",
            "position": "fixed",
            "top": "20%",
            "left": "30%",
            "width": "40%",
            "height": "40%",
            "backgroundColor": "white",
            "boxShadow": "0px 0px 10px rgba(0, 0, 0, 0.5)",
            "zIndex": 1000,
            "padding": "20px",
            "borderRadius": "10px",
        }

    return "", {"display": "none"}

# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)
