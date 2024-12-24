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

# Load shark incident data
df = pd.read_csv("shark.csv")  # Replace with the path to your dataset

# Filter for valid latitude and longitude points
df = df.dropna(subset=["Latitude", "Longitude"])
df["Date"] = pd.to_datetime(df["Incident.year"].astype(str) + "-" + df["Incident.month"].astype(str), errors="coerce")

# Remove None or NaN values in "Shark.common.name" for dropdown options
species_options = [
    {"label": species, "value": species}
    for species in df["Shark.common.name"].dropna().unique()
]

# Layout of Dash App
app.layout = html.Div(
    children=[
        html.Div(
            className="row",
            children=[
                # Column for user controls
                html.Div(
                    className="four columns div-user-controls",
                    children=[
                        html.H2("DASH - SHARK INCIDENT DATA"),
                        html.P(
                            "Select different days using the date picker or by selecting "
                            "different time frames on the histogram."
                        ),
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
                        # Dropdown for shark species
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
                # Column for app graphs and plots
                html.Div(
                    className="eight columns div-for-charts bg-grey",
                    children=[
                        dcc.Graph(id="map-graph", config={"scrollZoom":True}),  # Bubble map visualization
                         html.Div(
                            id="incident-details",
                            style={
                                "position": "absolute",
                                "top": "20px",
                                "right": "100px",
                                "border": "1px solid #ccc",
                                "padding": "10px",
                                "backgroundColor": "#f9f9f9",
                                "boxShadow": "0px 4px 10px rgba(0, 0, 0, 0.1)",
                                "display": "none",  # Initially hidden
                                "zIndex": 10,  # Ensure it appears above other content
                                "width": "300px",
                            },
                        ),
                        html.Div(
                            id="blank-widget",
                            style={
                                "border": "2px dashed #ccc",  # Optional styling to make it visible
                                "padding": "20px",
                                "margin": "10px",
                                "height": "50px",
                                "width": "50px",
                                "textAlign": "center",
                                "display": "flex",
                                "justifyContent": "center",
                                "alignItems": "center",
                            },
                            children="This is a blank widget",  # Optional placeholder text
                        ),
                        html.Button("Clear Widget", id="clear-button"),
                    ]
                ),
            ],
        )
    ]
)

# Update Map Graph based on date-picker and selected species
@app.callback(
    Output("map-graph", "figure"),
    [Input("date-picker", "date"), Input("species-dropdown", "value")],
)
def update_graph(datePicked, selectedSpecies):
    date_picked = pd.to_datetime(datePicked)
    filtered_df = df[(df["Date"].dt.month == date_picked.month) & (df["Date"].dt.day == date_picked.day)]

    if selectedSpecies:
        filtered_df = filtered_df[filtered_df["Shark.common.name"] == selectedSpecies]

    # Aggregate data by Latitude and Longitude to get incident counts per location
    bubble_data = filtered_df.groupby(["Latitude", "Longitude"]).size().reset_index(name="Incident Count")

    # Create bubble map using Plotly Express
    fig = px.scatter_mapbox(
        bubble_data,
        lat="Latitude",
        lon="Longitude",
        size="Incident Count",  # Bubble size based on the count of incidents
        hover_name="Incident Count",
        color_discrete_sequence=["blue"],  # Customize color if needed
        zoom=4,
        center={"lat": -25.0, "lon": 133.0},  # Center on Australia
        mapbox_style="open-street-map",
    )

    fig.update_layout(
        title="Shark Incidents Density",
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
    )

    return fig

@app.callback(
    [Output("incident-details", "children"), Output("incident-details", "style")],
    [Input("map-graph", "clickData")],
)

def display_incident_details(clickData):
    # Log the received clickData to the console
    print("DEBUG: Received clickData =", clickData)

    if clickData is None:
        return "", {"display": "none"}  # Hide the widget when no click

    try:
        lat = clickData["points"][0]["lat"]
        lon = clickData["points"][0]["lon"]
    except (KeyError, IndexError) as e:
        print("DEBUG: Error accessing clickData", e)
        return "Error reading incident data.", {"display": "block"}

    incidents = df[(df["Latitude"] == lat) & (df["Longitude"] == lon)]
    print("DEBUG: Filtered incidents =", incidents)

    if incidents.empty:
        return "No incidents found for this location.", {"display": "block"}

    details = [
        html.H4(f"Incidents at ({lat}, {lon})"),
        html.Ul([html.Li(f"{row['Date'].date()}: {row['Shark.common.name']}") for _, row in incidents.iterrows()]),
    ]

    return details, {"display": "block"}

if __name__ == "__main__":
    app.run_server(debug=True)
