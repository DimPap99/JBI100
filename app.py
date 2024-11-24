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

# Load and preprocess shark incident data
df = pd.read_csv("shark.csv")  # Replace with the path to your dataset
def clean_coordinates(value):
    if isinstance(value, str) and value.endswith('.'):
        value = value[:-1]  # Remove trailing dot
    try:
        return float(value)
    except ValueError:
        return None  # Mark invalid values as None

df["Latitude"] = df["Latitude"].apply(clean_coordinates)
df["Longitude"] = df["Longitude"].apply(clean_coordinates)
# Ensure valid latitude and longitude points
df = df.dropna(subset=["Latitude", "Longitude"])

# Convert Date column
df["Date"] = pd.to_datetime(df["Incident.year"].astype(str) + "-" + df["Incident.month"].astype(str), errors="coerce")

# Dropdown options for shark species
species_options = [
    {"label": species, "value": species}
    for species in df["Shark.common.name"].dropna().unique()
]

# Sample shark images (replace with actual URLs or paths)
shark_images = {
    "Great White Shark": "https://example.com/great_white.jpg",
    "Tiger Shark": "https://example.com/tiger_shark.jpg",
    "Bull Shark": "https://example.com/bull_shark.jpg",
    "Other": "https://example.com/default_shark.jpg",
}

# Layout of the app
app.layout = html.Div(
    children=[
        dcc.Store(id="selected-shark", data=None),  # Store for selected shark data
        html.Div(
            className="row",
            children=[
                # Column for user controls
                html.Div(
                    className="four columns div-user-controls",
                    children=[
                        html.H2("DASH - SHARK INCIDENT DATA"),
                        html.P("Select different days using the date picker or by selecting different time frames."),
                        html.Div(
                            className="div-for-dropdown",
                            children=[
                                dcc.DatePickerSingle(
                                    id="date-picker",
                                    min_date_allowed=dt(1791, 1, 1),
                                    max_date_allowed=dt(2022, 12, 31),
                                    initial_visible_month=dt(2022, 1, 1),
                                    date=dt(2022, 1, 1).date(),
                                    display_format="MMMM D, YYYY",
                                    style={"border": "0px solid black"},
                                )
                            ],
                        ),
                        dcc.Dropdown(
                            id="species-dropdown",
                            options=species_options,
                            placeholder="Select a Shark Species",
                        ),
                        html.P(id="total-incidents"),
                        dcc.Markdown(
                            """
                            Source: [Australian Shark-Incident Database](https://github.com/cjabradshaw/AustralianSharkIncidentDatabase)
                            """
                        ),
                    ],
                ),
                # Column for graphs and charts
                html.Div(
                    className="eight columns div-for-charts bg-grey",
                    children=[
                        dcc.Graph(id="map-graph", config={"scrollZoom": True}),  # Map visualization
                    ],
                ),
            ],
        ),
        # Modal for displaying detailed information
        html.Div(
            id="info-modal",
            style={
                "display": "none",
                "position": "fixed",
                "top": 0,
                "right": 0,
                "width": "30%",
                "height": "100%",
                "backgroundColor": "white",
                "boxShadow": "0px 0px 10px rgba(0, 0, 0, 0.5)",
                "zIndex": 1000,
                "overflowY": "scroll",
            },
            children=[
                html.Button("Close", id="close-modal", style={"float": "right", "margin": "10px"}),
                html.Div(id="shark-details", style={"padding": "20px"}),  # Shark details
            ],
        ),
    ]
)


@app.callback(
    Output("map-graph", "figure"),
    [Input("date-picker", "date"), Input("species-dropdown", "value"), Input("map-graph", "clickData")],
)
def update_graph(datePicked, selectedSpecies, clickData):
    # Filter data by selected date
    date_picked = pd.to_datetime(datePicked)
    filtered_df = df[(df["Date"].dt.month == date_picked.month) & (df["Date"].dt.day == date_picked.day)]

    if selectedSpecies:
        filtered_df = filtered_df[filtered_df["Shark.common.name"] == selectedSpecies]

    # Aggregate data for bubble map
    bubble_data = filtered_df.groupby(["Latitude", "Longitude"]).size().reset_index(name="Incident Count")

    # Default map settings
    zoom_level = 4
    center = {"lat": -25.0, "lon": 133.0}

    # Update map settings if a bubble is clicked
    if clickData:
        clicked_point = clickData["points"][0]
        center = {"lat": float(clicked_point["lat"]), "lon": float(clicked_point["lon"])}
        zoom_level = 8

    # Create the map figure
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
   [Output("info-modal", "style"), Output("shark-details", "children")],
    [Input("map-graph", "clickData")],
)
def show_shark_info(clickData):
    # ctx = dash.callback_context
    # triggered_input = ctx.triggered[0]["prop_id"]
    # print("Triggered Input:", triggered_input)  # Debugging

    # if "close-modal" in triggered_input:
    #     print("Modal closed.")  # Debugging
    #     return {"display": "none"}, current_details

    # if clickData:
    #     print("ClickData:", clickData)  # Debugging

    #     clicked_point = clickData["points"][0]
    #     latitude = float(clicked_point["lat"])
    #     longitude = float(clicked_point["lon"])

    #     # Use a small tolerance to handle floating-point precision
    #     tolerance = 1e-6
    #     incidents = df[
    #         (df["Latitude"].astype(float).sub(latitude).abs() <= tolerance) &
    #         (df["Longitude"].astype(float).sub(longitude).abs() <= tolerance)
    #     ]
    #     print("Filtered Incidents:", incidents)  # Debugging

    #     if incidents.empty:
    #         print("No incidents found.")  # Debugging
    #         return {"display": "none"}, html.Div("No data available for this location.")

    #     species = incidents["Shark.common.name"].iloc[0]
    #     details = html.Div([
    #         html.H2(f"Shark Species: {species}"),
    #         html.P(f"Total Incidents: {len(incidents)}"),
    #         html.P(f"Latitude: {latitude}, Longitude: {longitude}"),
    #     ])

    #     print("Returning modal with details.")  # Debugging
    #     return {"display": "block"}, details

    # print("No ClickData received.")  # Debugging
    # return {"display": "none"}, current_details

    return {"display": "block"}, html.Div("Test Content")

if __name__ == "__main__":
    app.run_server(debug=True)
