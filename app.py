import dash
from dash import dcc, html
import pandas as pd
from dash.dependencies import Input, Output
import plotly.express as px
from datetime import datetime as dt

# Initialize the Dash app
app = dash.Dash(__name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}])
app.title = "Shark Incidents in Australia"
server = app.server

# Load and preprocess shark incident data
df = pd.read_csv("shark.csv")  # Replace with the path to your dataset
df = df.dropna(subset=["Latitude", "Longitude"])  # Ensure valid Latitude and Longitude
df["Date"] = pd.to_datetime(df["Incident.year"].astype(str) + "-" + df["Incident.month"].astype(str), errors="coerce")

# Dropdown options for shark species
species_options = [
    {"label": species, "value": species}
    for species in df["Shark.common.name"].dropna().unique()
]

# Layout of the app
app.layout = html.Div(
    children=[
        html.Div(
            className="row",
            children=[
                html.Div(
                    className="four columns div-user-controls",
                    children=[
                        html.H2("DASH - SHARK INCIDENT DATA"),
                        html.P("Select different days using the date picker."),
                        dcc.DatePickerSingle(
                            id="date-picker",
                            min_date_allowed=dt(1791, 1, 1),
                            max_date_allowed=dt(2022, 12, 31),
                            initial_visible_month=dt(2022, 1, 1),
                            date=dt(2022, 1, 1).date(),
                            display_format="MMMM D, YYYY",
                        ),
                        dcc.Dropdown(
                            id="species-dropdown",
                            options=species_options,
                            placeholder="Select a Shark Species",
                        ),
                    ],
                ),
                html.Div(
                    className="eight columns div-for-charts bg-grey",
                    children=[
                        dcc.Graph(id="map-graph", config={"scrollZoom": True}),
                    ],
                ),
            ],
        ),
        # Modal for displaying an empty modal
        html.Div(
            id="info-modal",
            style={
                "display": "none",  # Initially hidden
                "position": "fixed",
                "top": "20%",
                "left": "30%",
                "width": "40%",
                "height": "40%",
                "backgroundColor": "white",
                "boxShadow": "0px 0px 10px rgba(0, 0, 0, 0.5)",
                "zIndex": 1000,  # Ensure it is above other elements
                "padding": "20px",
                "borderRadius": "10px",
            },
            children=[
                html.Button("Close", id="close-modal", style={"float": "right", "margin": "10px"}),
                html.Div("This is an empty modal"),  # Empty modal content
            ],
        ),
    ]
)


@app.callback(
    Output("map-graph", "figure"),
    [Input("date-picker", "date"), Input("species-dropdown", "value"), Input("map-graph", "clickData")],
)
def update_graph(datePicked, selectedSpecies, clickData):
    date_picked = pd.to_datetime(datePicked)
    filtered_df = df[(df["Date"].dt.month == date_picked.month) & (df["Date"].dt.day == date_picked.day)]

    if selectedSpecies:
        filtered_df = filtered_df[filtered_df["Shark.common.name"] == selectedSpecies]

    bubble_data = filtered_df.groupby(["Latitude", "Longitude"]).size().reset_index(name="Incident Count")
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
    fig.update_layout(title="Shark Incidents Density", margin={"r": 0, "t": 0, "l": 0, "b": 0})
    return fig

@app.callback(
    Output("info-modal", "style"),
    [Input("map-graph", "clickData"), Input("close-modal", "n_clicks")],
)
def toggle_modal(clickData, close_clicks):
    ctx = dash.callback_context
    triggered_input = ctx.triggered[0]["prop_id"]

    if "close-modal" in triggered_input:
        return {"display": "none"}  # Close the modal

    if "map-graph.clickData" in triggered_input:
        return {
            "display": "block",  # Open modal
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

    return {"display": "none"}  # Default state


if __name__ == "__main__":
    app.run_server(debug=True)
