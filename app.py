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
# df["Date"] = pd.to_datetime(
#     df["Incident.year"].astype(str) + "-" + df["Incident.month"].astype(str),
#     errors="coerce"
# )

# Build the list of species for the dropdown
species_options = [
    {"label": species, "value": species}
    for species in df["Shark.common.name"].dropna().unique()
]

df["Latitude"] = pd.to_numeric(df["Latitude"], errors="coerce")
df["Longitude"] = pd.to_numeric(df["Longitude"], errors="coerce")

# Define start and end dates for RangeSlider
df = df.dropna(subset=["Date"])  # Ensure no missing values in Date
df["Date"] = pd.to_datetime(df["Date"], errors="coerce")  # Handle parsing errors
start_year = int(df["Date"].dt.year.min())  # Convert to integer
end_year = int(df["Date"].dt.year.max())
years = list(range(start_year, end_year + 1))

# -----------------------
# App Layout
# -----------------------
app.layout = html.Div([
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
                    dcc.RangeSlider(
                        id='date-slider',
                        min=start_year,
                        max=end_year,
                        value=[start_year, end_year],
                        marks={year: str(year) for year in range(start_year, end_year + 1, 50)},
                        step = 1
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
    
    # Store that will hold the incidents for the clicked lat/lon
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

# ------------------------------------------------------
# Callback #1: Update the main map based on user inputs
# ------------------------------------------------------
@app.callback(
    Output("map-graph", "figure"),
    Input("date-slider", "value"),
    Input("date-picker", "date"),
    Input("species-dropdown", "value"),
    Input("map-graph", "clickData"),
)
def update_graph(date_picked, year_range, selectedSpecies, clickData):
    # Filter data for selected month/day
    # Default: Full dataset
    filtered_df = df.copy()

    # Determine which input triggered the callback
    ctx = dash.callback_context
    if not ctx.triggered:
        triggered_input = None
    else:
        triggered_input = ctx.triggered[0]["prop_id"].split(".")[0]

    # Apply filters based on the active input
    if triggered_input == "date-picker" and date_picked:
        # Filter by specific date
        date_picked = pd.to_datetime(date_picked)
        filtered_df = filtered_df[
            (filtered_df["Date"].dt.month == date_picked.month)
            & (filtered_df["Date"].dt.day == date_picked.day)
        ]
    elif triggered_input == "date-slider" and year_range:
        # Filter by year range
        start_year, end_year = year_range
        filtered_df = filtered_df[
            (filtered_df["Date"].dt.year >= start_year)
            & (filtered_df["Date"].dt.year <= end_year)
        ]



    # Filter by species if selected
    if selectedSpecies:
        filtered_df = filtered_df[filtered_df["Shark.common.name"] == selectedSpecies]

    # Group by lat/lon to create bubble size
    bubble_data = filtered_df.groupby(
        ["Latitude", "Longitude"]
    ).size().reset_index(name="Incident Count")

    # Default map center & zoom (Australia)
    zoom_level = 4
    center = {"lat": -25.0, "lon": 133.0}

    # If user clicked a bubble, zoom in
    if clickData:
        clicked_point = clickData["points"][0]
        center = {"lat": float(clicked_point["lat"]), "lon": float(clicked_point["lon"])}
        zoom_level = 8

    # Create the figure
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

# -----------------------------------------------------------------------
# Callback #2 (Unified):
#   - Determines whether to open/close the modal
#   - Updates 'selected-incidents-store' data
#   - Updates the 'modal-incident-content' children
#   - We do it all in ONE callback to avoid "Output is already in use"
# -----------------------------------------------------------------------
@app.callback(
    Output("info-modal", "style"),
    Output("selected-incidents-store", "data"),
    Output("modal-incident-content", "children"),
    [
        Input("map-graph", "clickData"),
        Input("close-modal", "n_clicks"),
        Input("prev-incident", "n_clicks"),
        Input("next-incident", "n_clicks")
    ],
    [State("selected-incidents-store", "data")]
)
def handle_modal_and_incidents(clickData, close_clicks, prev_clicks, next_clicks, store_data):
    """
    - If the user clicks a bubble, we open the modal & load all incidents for that lat/lon into store_data.
    - If the user clicks close, we hide the modal & reset store_data.
    - If the user clicks Prev/Next, we move the current_index up/down.
    - We return (modal style, updated store_data, modal content) in one shot.
    """
    # Default values
    default_style = {"display": "none"}
    default_store = {"rows": [], "current_index": 0}
    default_content = "No incident data available"

    # Figure out which input fired
    ctx = dash.callback_context
    if not ctx.triggered:
        return default_style, default_store, default_content

    triggered_input = ctx.triggered[0]["prop_id"]

    # 1) If close button was clicked -> hide modal & reset store
    if "close-modal" in triggered_input:
        return default_style, default_store, default_content

    # 2) If the map was clicked -> open modal and store the lat/lon incidents
    if "map-graph.clickData" in triggered_input and clickData:
        lat_clicked = clickData["points"][0]["lat"]
        lon_clicked = clickData["points"][0]["lon"]
        # Filter df for that lat/lon (watch out for float precision if needed)
        filtered_incidents = df[
            (df["Latitude"] == float(lat_clicked)) &
            (df["Longitude"] == float(lon_clicked))
        ]
        rows = []
        for _, row in filtered_incidents.iterrows():
            rows.append({
                "Shark.common.name": row.get("Shark.common.name", "Unknown"),
                "Date": (row["Date"].date().isoformat()
                         if pd.notnull(row["Date"]) else "Unknown"),
                "Victim.injury": str(row.get("Victim.injury", "")),
                "Provoked/unprovoked": str(row.get("Provoked/unprovoked", "")),
            })
        new_store = {"rows": rows, "current_index": 0}
        # Build content for the first incident
        if rows:
            first = rows[0]
            content = [
                html.P(f"Shark.common.name: {first['Shark.common.name']}"),
                html.P(f"Date: {first['Date']}"),
                html.P(f"Victim.injury: {first['Victim.injury']}"),
                html.P(f"Provoked/unprovoked: {first['Provoked/unprovoked']}"),
                html.P(f"Showing 1 of {len(rows)}"),
            ]
        else:
            content = "No incident data available"

        modal_style = {
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
        return modal_style, new_store, content

    # 3) If Prev/Next was clicked -> update the current_index in store_data
    rows = store_data.get("rows", [])
    current_idx = store_data.get("current_index", 0)
    if not rows:
        # Nothing to show
        return default_style, default_store, default_content

    # The modal is presumably open if we have data in the store
    modal_style = {
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

    if "prev-incident" in triggered_input:
        current_idx = max(0, current_idx - 1)
    elif "next-incident" in triggered_input:
        current_idx = min(len(rows) - 1, current_idx + 1)

    updated_store = {"rows": rows, "current_index": current_idx}
    incident = rows[current_idx]
    content = [
        html.P(f"Shark.common.name: {incident['Shark.common.name']}"),
        html.P(f"Date: {incident['Date']}"),
        html.P(f"Victim.injury: {incident['Victim.injury']}"),
        html.P(f"Provoked/unprovoked: {incident['Provoked/unprovoked']}"),
        html.P(f"Showing {current_idx+1} of {len(rows)}"),
    ]

    return modal_style, updated_store, content

# -------------
# Run the app
# -------------
if __name__ == "__main__":
    app.run_server(debug=True)
