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

# Create date indices for RangeSlider
df = df.sort_values("Date")
unique_dates = df["Date"].dropna().sort_values().unique()
date_to_index = {date: i for i, date in enumerate(unique_dates)}
index_to_date = {i: date for i, date in enumerate(unique_dates)}

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
        id="background-container",
        children=[
            html.Div(
                className="row",
                children=[
                    # Left column with controls
                    html.Div(
                        className="four columns div-user-controls",
                        children=[
                            html.H2("DASH - SHARK INCIDENT DATA"),
                            html.P("Select a date range to filter incidents."),
                            html.Div([
                                html.Label("Start Date:"),
                                dcc.Input(
                                    id="start-date-input",
                                    type="text",
                                    placeholder="YYYY-MM-DD",
                                    value=str(unique_dates[0].date()),
                                    style={"marginRight": "10px", "width": "120px"}
                                ),
                                html.Label("End Date:"),
                                dcc.Input(
                                    id="end-date-input",
                                    type="text",
                                    placeholder="YYYY-MM-DD",
                                    value=str(unique_dates[-1].date()),
                                    style={"marginRight": "10px", "width": "120px"}
                                ),
                                html.Button("Apply", id="apply-date-button", n_clicks=0, style={"marginLeft": "10px"})
                            ], style={"marginBottom": "15px", "display": "flex", "alignItems": "center"}),
                            dcc.RangeSlider(
                                id="date-slider",
                                min=0,
                                max=len(unique_dates) - 1,
                                value=[0, len(unique_dates) - 1],
                                marks={
                                    i: str(index_to_date[i].year)
                                    for i in range(0, len(unique_dates), 50)  # Uniform intervals of 50 indices
    
                                },
                                tooltip={"placement": "bottom", "always_visible": True},
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
])

# Synchronize inputs and slider
@app.callback(
    [Output("start-date-input", "value"),
     Output("end-date-input", "value"),
     Output("date-slider", "value")],
    [Input("apply-date-button", "n_clicks")],
    [State("start-date-input", "value"),
     State("end-date-input", "value"),
     State("date-slider", "value")]
)
def synchronize_inputs_and_slider(n_clicks, start_date, end_date, slider_range):
    if n_clicks == 0:
        raise dash.exceptions.PreventUpdate

    # Initialize start and end indices based on current slider range
    start_idx = slider_range[0]
    end_idx = slider_range[1]

    try:
        # Parse start date from input
        start_idx = date_to_index[pd.to_datetime(start_date)]
    except Exception:
        start_date = index_to_date[start_idx].strftime("%Y-%m-%d")

    try:
        # Parse end date from input
        end_idx = date_to_index[pd.to_datetime(end_date)]
    except Exception:
        end_date = index_to_date[end_idx].strftime("%Y-%m-%d")

    # Ensure indices are within range
    start_idx = max(0, min(start_idx, len(unique_dates) - 1))
    end_idx = max(0, min(end_idx, len(unique_dates) - 1))

    # Finalize start and end dates
    start_date = index_to_date[start_idx].strftime("%Y-%m-%d")
    end_date = index_to_date[end_idx].strftime("%Y-%m-%d")

    return start_date, end_date, [start_idx, end_idx]

# Update the map based on slider and species selection
@app.callback(
    Output("map-graph", "figure"),
    [Input("date-slider", "value"),
     Input("species-dropdown", "value")]
)
def update_map(slider_range, selected_species):
    start_date = index_to_date[slider_range[0]]
    end_date = index_to_date[slider_range[1]]

    filtered_df = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)]

    if selected_species:
        filtered_df = filtered_df[filtered_df["Shark.common.name"] == selected_species]

    bubble_data = filtered_df.groupby(["Latitude", "Longitude"]).size().reset_index(name="Incident Count")

    fig = px.scatter_mapbox(
        bubble_data,
        lat="Latitude",
        lon="Longitude",
        size="Incident Count",
        hover_name="Incident Count",
        color_discrete_sequence=["#636EFA"],
        zoom=4,
        center={"lat": -25.0, "lon": 133.0},
        mapbox_style="open-street-map",
    )
    fig.update_traces(marker=dict(opacity=0.5))
    fig.update_layout(
        title="Shark Incidents Density",
        margin={"r": 0, "t": 0, "l": 0, "b": 0}
    )
    return fig

if __name__ == "__main__":
    app.run_server(debug=True)
