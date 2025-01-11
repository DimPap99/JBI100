import dash
from dash import dcc, html
import pandas as pd
from dash.dependencies import Input, Output, State
import plotly.express as px
from datetime import datetime as dt

# ------------------------------------------------------------------------------
# Initialize the app
# ------------------------------------------------------------------------------
app = dash.Dash(__name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}])
app.title = "Shark Incidents in Australia"
server = app.server

# ------------------------------------------------------------------------------
# Load & Preprocess Data
# ------------------------------------------------------------------------------
df = pd.read_csv("shark.csv")  # <-- Adjust CSV path as needed

# Convert lat/lon to numeric floats
df["Latitude"] = pd.to_numeric(df["Latitude"], errors="coerce")
df["Longitude"] = pd.to_numeric(df["Longitude"], errors="coerce")

# Drop invalid lat/lon
df.dropna(subset=["Latitude", "Longitude"], inplace=True)

# Round lat/lon to avoid tiny float mismatches
df["Latitude"] = df["Latitude"].round(5)
df["Longitude"] = df["Longitude"].round(5)

# Create a datetime from Incident.year + Incident.month
df["Date"] = pd.to_datetime(
    df["Incident.year"].astype(str) + "-" + df["Incident.month"].astype(str),
    errors="coerce"
)

# Build the species dropdown
species_options = [
    {"label": s, "value": s}
    for s in df["Shark.common.name"].dropna().unique()
]

# ------------------------------------------------------------------------------
# Species -> Image Filename Mapping
# (Adjust to match your actual filenames in assets/images/)
# ------------------------------------------------------------------------------
species_image_map = {
    "grey reef shark": "gray-reef-shark.webp",
    "dogfish": "dogfish.webp",
    "bull shark": "bull_shark.webp",
    "grey nurse shark": "Nurse-shark.webp",
    "blacktip reef shark": "blacktip_reef_shark.jpg",
    "shortfin mako shark": "Shortfin-mako-shark.webp",
    "galapagos shark": "Galapagos-shark.jpg",
    "port jackson shark": "port_Jackson_shark.jpg",
    "wobbegong": "wobbegong.webp",
    "whitetip reef shark": "white-tip-shark.jpeg",
    "school shark": "school-shark.jpg",
    "whaler shark": "bronze-whaler-shark.jpeg",
    "dusky shark": "dusky-shark.webp",
    "hammerhead shark": "Hammerhead-shark.webp",  # removed trailing space
    "blind shark": "Blindshark.jpg",
    "bronze whaler shark": "bronze-whaler-shark.jpeg",
    "white shark": "White-shark.webp",
    "broadnose sevengill shark": "Broadnose-sevengill-shark.webp",
    "unknown": "unknown.webp",
    "silvertip shark": "silvertip-shark.webp",
    "seven gill shark": "sevengill-shark.jpg",
    "tiger shark": "tiger_shark.jpg",
    "sevengill shark": "sevengill-shark.jpg",
    "lemon shark": "lemon-shark.jpg",
    # fallback if species not found
}

def get_shark_image(species_name: str) -> str:
    """Return the filename for the shark image, default to 'unknown.webp' if no match."""
    if not species_name:
        return "unknown.webp"
    clean = species_name.strip().lower()
    return species_image_map.get(clean, "unknown.webp")

# ------------------------------------------------------------------------------
# Layout
# ------------------------------------------------------------------------------
app.layout = html.Div([
    html.Div(
        className="row",
        children=[
            # Left Column (Controls)
            html.Div(
                className="four columns div-user-controls",
                children=[
                    html.H2("DASH - SHARK INCIDENT DATA"),
                    html.P("Select a date (month/day) to filter incidents."),
                    dcc.DatePickerSingle(
                        id="date-picker",
                        min_date_allowed=dt(1791, 1, 1),
                        max_date_allowed=dt(2022, 12, 31),
                        # Example: set an initial date that actually has data
                        initial_visible_month=dt(1803, 3, 1),
                        date=dt(1803, 3, 1).date(),
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
            # Right Column (Map)
            html.Div(
                className="eight columns div-for-charts bg-grey",
                children=[
                    dcc.Graph(id="map-graph", config={"scrollZoom": True}),
                ],
            ),
        ],
    ),

    # A hidden Store that holds the incidents for the clicked bubble
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
            "height": "auto",
            "backgroundColor": "white",
            "boxShadow": "0px 0px 10px rgba(0, 0, 0, 0.5)",
            "zIndex": 1000,
            "padding": "20px",
            "borderRadius": "10px",
        },
        children=[
            html.Button("Close", id="close-modal", style={"float": "right", "margin": "10px"}),
            html.Div(
                style={"marginBottom": "10px", "textAlign": "center"},
                children=[
                    html.Button("Previous", id="prev-incident", n_clicks=0,
                                style={"marginRight": "20px", "padding": "8px 16px"}),
                    html.Button("Next", id="next-incident", n_clicks=0,
                                style={"padding": "8px 16px"}),
                ],
            ),
            html.Div(id="modal-incident-content"),
        ],
    ),
])

# ------------------------------------------------------------------------------
# Callback 1: Build the main Map figure from the Date & Species filters
# ------------------------------------------------------------------------------
@app.callback(
    Output("map-graph", "figure"),
    [
        Input("date-picker", "date"),
        Input("species-dropdown", "value")
    ],
)
def update_map(datePicked, selectedSpecies):
    # Filter by date (month/day)
    date_picked = pd.to_datetime(datePicked) if datePicked else None
    if date_picked:
        # If your dataset doesn't have day-level detail, you can adapt here
        filtered_df = df[
            (df["Date"].dt.month == date_picked.month) &
            (df["Date"].dt.day == date_picked.day)
        ]
    else:
        filtered_df = df.copy()

    # Filter by species if selected
    if selectedSpecies:
        filtered_df = filtered_df[filtered_df["Shark.common.name"] == selectedSpecies]

    if filtered_df.empty:
        # Return an empty figure if no data
        return px.scatter_mapbox(
            pd.DataFrame({"Latitude": [], "Longitude": [], "Incident Count": []}),
            lat="Latitude", lon="Longitude", size="Incident Count",
            zoom=4, center={"lat": -25.0, "lon": 133.0},
            mapbox_style="open-street-map"
        )

    # Group to get bubble sizes
    bubble_data = filtered_df.groupby(["Latitude", "Longitude"]).size().reset_index(name="Incident Count")

    # Create the figure
    fig = px.scatter_mapbox(
        bubble_data,
        lat="Latitude",
        lon="Longitude",
        size="Incident Count",
        hover_name="Incident Count",
        color_discrete_sequence=["#636EFA"],
        zoom=4,                        # default zoom
        center={"lat": -25.0, "lon": 133.0},   # center on Australia
        mapbox_style="open-street-map"
    )
    fig.update_traces(marker=dict(opacity=0.5))
    fig.update_layout(
        title="Shark Incidents Density",
        margin={"r": 0, "t": 0, "l": 0, "b": 0}
    )
    return fig

# ------------------------------------------------------------------------------
# Callback 2 (Unified): 
#   - Re-applies Date + Species filters so only displayed incidents appear
#   - Filters for the clicked lat/lon
#   - Opens/closes the modal
#   - Handles Next/Previous
# ------------------------------------------------------------------------------
@app.callback(
    Output("info-modal", "style"),
    Output("selected-incidents-store", "data"),
    Output("modal-incident-content", "children"),
    [
        Input("date-picker", "date"),
        Input("species-dropdown", "value"),
        Input("map-graph", "clickData"),
        Input("close-modal", "n_clicks"),
        Input("prev-incident", "n_clicks"),
        Input("next-incident", "n_clicks"),
    ],
    [State("selected-incidents-store", "data")]
)
def handle_modal_and_incidents(
    datePicked, selectedSpecies, clickData,
    close_clicks, prev_clicks, next_clicks,
    store_data
):
    """Open/close modal and cycle through incidents that pass the date+species filter + lat/lon."""
    ctx = dash.callback_context
    if not ctx.triggered:
        return {"display": "none"}, {"rows": [], "current_index": 0}, "No incident data available"

    triggered_id = ctx.triggered[0]["prop_id"]

    # Default style, store, content if nothing is found
    default_style = {"display": "none"}
    default_store = {"rows": [], "current_index": 0}
    default_content = html.Div("No incident data available")

    # 1) If the user clicked the Close button
    if "close-modal" in triggered_id:
        return default_style, default_store, default_content

    # ---------------------------------------------------------
    # First, apply the same date+species filters to the DataFrame
    # so we only show incidents that appear on the map
    # ---------------------------------------------------------
    date_picked = pd.to_datetime(datePicked) if datePicked else None
    if date_picked:
        filter_df = df[
            (df["Date"].dt.month == date_picked.month) &
            (df["Date"].dt.day == date_picked.day)
        ]
    else:
        filter_df = df.copy()

    if selectedSpecies:
        filter_df = filter_df[filter_df["Shark.common.name"] == selectedSpecies]

    # 2) If the map was clicked -> gather lat/lon from clickData,
    #    filter further by lat/lon, and open the modal
    if "map-graph.clickData" in triggered_id and clickData:
        lat_clicked = round(clickData["points"][0]["lat"], 5)
        lon_clicked = round(clickData["points"][0]["lon"], 5)

        clicked_incidents = filter_df[
            (filter_df["Latitude"] == lat_clicked) &
            (filter_df["Longitude"] == lon_clicked)
        ]

        rows = []
        for _, row in clicked_incidents.iterrows():
            species = row.get("Shark.common.name", "Unknown")
            date_str = (
                row["Date"].date().isoformat() 
                if pd.notnull(row["Date"]) else "Unknown"
            )
            rows.append({
                "Shark.common.name": species,
                "Date": date_str,
                "Victim.injury": str(row.get("Victim.injury", "")),
                "Provoked/unprovoked": str(row.get("Provoked/unprovoked", "")),
            })

        if not rows:
            # No data -> show "No incident data"
            return default_style, default_store, default_content

        new_store = {"rows": rows, "current_index": 0}
        content = build_modal_content(rows, 0)

        modal_style = {
            "display": "block",
            "position": "fixed",
            "top": "20%",
            "left": "30%",
            "width": "40%",
            "height": "auto",
            "backgroundColor": "white",
            "boxShadow": "0px 0px 10px rgba(0, 0, 0, 0.5)",
            "zIndex": 1000,
            "padding": "20px",
            "borderRadius": "10px",
        }
        return modal_style, new_store, content

    # 3) If Prev/Next was clicked -> update current_index in store
    rows = store_data.get("rows", [])
    current_idx = store_data.get("current_index", 0)
    if not rows:
        # No data to show
        return default_style, default_store, default_content

    # The modal remains open if we have data
    modal_style = {
        "display": "block",
        "position": "fixed",
        "top": "20%",
        "left": "30%",
        "width": "40%",
        "height": "auto",
        "backgroundColor": "white",
        "boxShadow": "0px 0px 10px rgba(0, 0, 0, 0.5)",
        "zIndex": 1000,
        "padding": "20px",
        "borderRadius": "10px",
    }

    if "prev-incident" in triggered_id:
        current_idx = max(0, current_idx - 1)
    elif "next-incident" in triggered_id:
        current_idx = min(len(rows) - 1, current_idx + 1)

    updated_store = {"rows": rows, "current_index": current_idx}
    content = build_modal_content(rows, current_idx)

    return modal_style, updated_store, content

# ------------------------------------------------------------------------------
# Helper Function: Build the modal's content for a given incident row
# ------------------------------------------------------------------------------
def build_modal_content(rows, idx):
    """
    Renders text + shark image side-by-side for the given row.
    """
    if not rows or idx < 0 or idx >= len(rows):
        return html.Div("No incident data available")

    incident = rows[idx]
    species = incident["Shark.common.name"]
    date_str = incident["Date"]
    victim_injury = incident["Victim.injury"]
    provoked = incident["Provoked/unprovoked"]

    image_filename = get_shark_image(species)
    total = len(rows)

    return html.Div(
        className="modal-content-wrapper",
        children=[
            # Left (text information)
            html.Div(
                className="modal-text-wrapper",
                children=[
                    html.H3(species if species else "Unknown Species", className="modal-species-title"),
                    html.P(f"Date: {date_str}", className="modal-text"),
                    html.P(f"Victim Injury: {victim_injury}", className="modal-text"),
                    html.P(f"Provoked/Unprovoked: {provoked}", className="modal-text"),
                    html.P(f"Showing {idx + 1} of {total}", className="modal-pagination"),
                ]
            ),
            # Right (image)
            html.Div(
                className="modal-image-wrapper",
                children=html.Img(
                    src=f"/assets/images/{image_filename}",
                    className="modal-shark-image"
                )
            ),
        ]
    )

# ------------------------------------------------------------------------------
# Run the App
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    app.run_server(debug=True)
