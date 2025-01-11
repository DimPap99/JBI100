import dash
from dash import dcc, html
import pandas as pd
from dash.dependencies import Input, Output, State
import plotly.express as px
from datetime import datetime as dt

app = dash.Dash(__name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}])
app.title = "Shark Incidents in Australia"
server = app.server

# ------------------------------------------------------------------------------
# Load & Preprocess Data
# ------------------------------------------------------------------------------
df = pd.read_csv("shark.csv")  # <-- Adjust CSV path if needed

df["Latitude"] = pd.to_numeric(df["Latitude"], errors="coerce")
df["Longitude"] = pd.to_numeric(df["Longitude"], errors="coerce")
df.dropna(subset=["Latitude", "Longitude"], inplace=True)

df["Latitude"] = df["Latitude"].round(5)
df["Longitude"] = df["Longitude"].round(5)

df["Date"] = pd.to_datetime(
    df["Incident.year"].astype(str) + "-" + df["Incident.month"].astype(str),
    errors="coerce"
)

species_options = [
    {"label": s, "value": s}
    for s in df["Shark.common.name"].dropna().unique()
]

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
    "hammerhead shark": "Hammerhead-shark.webp",
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
}

def get_shark_image(species_name: str) -> str:
    if not species_name or not isinstance(species_name, str):
        return "unknown.webp"
    clean = species_name.strip().lower()
    return species_image_map.get(clean, "unknown.webp")


# ------------------------------------------------------------------------------
# Layout
# ------------------------------------------------------------------------------
app.layout = html.Div([

    # Everything in a container we can blur
    html.Div(
        id="background-container",
        children=[
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
                    # Right Column (Map + Charts)
                    html.Div(
                        className="eight columns div-for-charts bg-grey",
                        style={
                            "display": "flex",
                            "flexDirection": "column",
                            ### CHANGED: either remove fixed height or set to 100vh
                            "height": "100vh",
                            "padding": "10px",
                            ### CHANGED: allow scrolling if content is taller
                            "overflowY": "auto",
                        },
                        children=[
                            # Map (take ~50% vertical)
                            html.Div(
                                style={"flex": "0 0 50%", "marginBottom": "10px"},
                                children=[
                                    dcc.Graph(
                                        id="map-graph",
                                        config={"scrollZoom": True},
                                        style={"height": "100%", "width": "100%"}
                                    )
                                ]
                            ),
                            # Below map: space for two charts side by side OR stacked
                            #
                            # Example: If you want them stacked, each can be 50% in height:
                            html.Div(
                                style={
                                    "flex": "0 0 50%",  
                                    "marginTop": "5px",
                                    ### If you want them side-by-side, switch flexDirection to 'row'
                                    "display": "flex",
                                    "flexDirection": "row",
                                    "justifyContent": "space-between",
                                },
                                children=[
                                    # Chart 1 (your pie chart)
                                    html.Div(
                                        style={"flex": "1", "marginRight": "5px"},
                                        children=[
                                            html.H4(
                                                "Box-Selected Data (Pie Chart by Species)",
                                                style={"paddingLeft": "12px"}
                                            ),
                                            dcc.Graph(
                                                id="pie-chart",
                                                style={"height": "85%", "width": "100%"}
                                            )
                                        ]
                                    ),
                                    # Chart 2 (placeholder or future chart)
                                    html.Div(
                                        style={"flex": "1", "marginLeft": "5px"},
                                        children=[
                                            html.H4("Another Chart Placeholder", style={"paddingLeft": "12px"}),
                                            html.Div(
                                                "Put your second chart or any content here...",
                                                style={
                                                    "height": "85%",
                                                    "width": "100%",
                                                    "border": "1px dashed #999",
                                                    "display": "flex",
                                                    "alignItems": "center",
                                                    "justifyContent": "center"
                                                }
                                            )
                                        ]
                                    ),
                                ]
                            ),
                        ],
                    ),
                ],
            ),
        ],
    ),

    # Store for clicked bubble incidents
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
                    html.Button(
                        "Previous",
                        id="prev-incident",
                        n_clicks=0,
                        style={"marginRight": "20px", "padding": "8px 16px"}
                    ),
                    html.Button(
                        "Next",
                        id="next-incident",
                        n_clicks=0,
                        style={"padding": "8px 16px"}
                    ),
                ],
            ),
            html.Div(id="modal-incident-content"),
        ],
    ),
])

# ------------------------------------------------------------------------------
# 1) Build the main Map figure from Date/Species
# ------------------------------------------------------------------------------
@app.callback(
    Output("map-graph", "figure"),
    [
        Input("date-picker", "date"),
        Input("species-dropdown", "value")
    ],
)
def update_map(datePicked, selectedSpecies):
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

    if filter_df.empty:
        return px.scatter_mapbox(
            pd.DataFrame({"Latitude": [], "Longitude": [], "Incident Count": []}),
            lat="Latitude", lon="Longitude", size="Incident Count",
            zoom=4, center={"lat": -25.0, "lon": 133.0},
            mapbox_style="open-street-map"
        )

    bubble_data = filter_df.groupby(["Latitude", "Longitude"]).size().reset_index(name="Incident Count")

    fig = px.scatter_mapbox(
        bubble_data,
        lat="Latitude",
        lon="Longitude",
        size="Incident Count",
        hover_name="Incident Count",
        color_discrete_sequence=["#636EFA"],
        zoom=4,
        center={"lat": -25.0, "lon": 133.0},
        mapbox_style="open-street-map"
    )
    fig.update_traces(marker=dict(opacity=0.5))
    fig.update_layout(
        title="Shark Incidents Density",
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        dragmode="select"
    )
    return fig


# ------------------------------------------------------------------------------
# 2) Unified Callback for the Modal + Blur
# ------------------------------------------------------------------------------
@app.callback(
    Output("info-modal", "style"),
    Output("selected-incidents-store", "data"),
    Output("modal-incident-content", "children"),
    Output("prev-incident", "style"),
    Output("next-incident", "style"),
    Output("background-container", "className"),
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
    ctx = dash.callback_context
    if not ctx.triggered:
        return {"display": "none"}, {"rows": [], "current_index": 0}, "No incident data available", {}, {}, ""

    triggered_id = ctx.triggered[0]["prop_id"]

    # Defaults
    default_style = {"display": "none"}
    default_store = {"rows": [], "current_index": 0}
    default_content = html.Div("No incident data available")
    no_blur = ""
    blurred = "blurred"

    prev_style = {"marginRight": "20px", "padding": "8px 16px"}
    next_style = {"padding": "8px 16px"}

    # If user closed
    if "close-modal" in triggered_id:
        return default_style, default_store, default_content, prev_style, next_style, no_blur

    # Filter
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

    # If map clicked => open modal
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
                row["Date"].date().isoformat() if pd.notnull(row["Date"]) else "Unknown"
            )
            rows.append({
                "Shark.common.name": species,
                "Date": date_str,
                "Victim.injury": str(row.get("Victim.injury", "")),
                "Provoked/unprovoked": str(row.get("Provoked/unprovoked", "")),
            })

        if not rows:
            return default_style, default_store, default_content, prev_style, next_style, no_blur

        new_store = {"rows": rows, "current_index": 0}
        content = build_modal_content(rows, 0)

        # Next/Prev button logic
        prev_style, next_style = get_nav_button_styles(len(rows), 0, prev_style, next_style)

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
        return modal_style, new_store, content, prev_style, next_style, blurred

    # If Prev/Next
    rows = store_data.get("rows", [])
    current_idx = store_data.get("current_index", 0)
    if not rows:
        return default_style, default_store, default_content, prev_style, next_style, no_blur

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

    prev_style, next_style = get_nav_button_styles(len(rows), current_idx, prev_style, next_style)
    return modal_style, updated_store, content, prev_style, next_style, blurred


# ------------------------------------------------------------------------------
# Helper: Build the modal's content
# ------------------------------------------------------------------------------
def build_modal_content(rows, idx):
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
# Helper: Show/hide "Prev"/"Next" buttons
# ------------------------------------------------------------------------------
def get_nav_button_styles(num_rows, current_idx, prev_style, next_style):
    prev_style = prev_style.copy()
    next_style = next_style.copy()

    if num_rows <= 1:
        prev_style["display"] = "none"
        next_style["display"] = "none"
        return prev_style, next_style

    if current_idx == 0:
        prev_style["display"] = "none"
    else:
        prev_style.pop("display", None)

    if current_idx == num_rows - 1:
        next_style["display"] = "none"
    else:
        next_style.pop("display", None)

    return prev_style, next_style

# ------------------------------------------------------------------------------
# 3) Box-select => Update Pie Chart
# ------------------------------------------------------------------------------
@app.callback(
    Output("pie-chart", "figure"),
    Input("map-graph", "selectedData")
)
def update_pie_chart(selectedData):
    if not selectedData or "points" not in selectedData:
        empty_df = pd.DataFrame({"Shark.common.name": [], "Count": []})
        return px.pie(empty_df, names="Shark.common.name", values="Count", title="No Box Selection")

    points = selectedData["points"]
    if not points:
        empty_df = pd.DataFrame({"Shark.common.name": [], "Count": []})
        return px.pie(empty_df, names="Shark.common.name", values="Count", title="No Box Selection")

    lats = [round(pt["lat"], 5) for pt in points]
    lons = [round(pt["lon"], 5) for pt in points]
    filtered_df = df[df["Latitude"].isin(lats) & df["Longitude"].isin(lons)]
    if filtered_df.empty:
        empty_df = pd.DataFrame({"Shark.common.name": [], "Count": []})
        return px.pie(empty_df, names="Shark.common.name", values="Count", title="No Data for Selection")

    pie_data = filtered_df.groupby("Shark.common.name").size().reset_index(name="Count")
    fig = px.pie(pie_data, names="Shark.common.name", values="Count", title="Shark Species in Box-Selected Area")
    fig.update_traces(textposition='inside', textinfo='percent+label')
    return fig

# ------------------------------------------------------------------------------
# Run
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    app.run_server(debug=True)
