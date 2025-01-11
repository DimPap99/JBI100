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

# Sort for RangeSlider
df = df.sort_values("Date")
unique_dates = df["Date"].dropna().unique()
date_to_index = {date: i for i, date in enumerate(unique_dates)}
index_to_date = {i: date for i, date in enumerate(unique_dates)}

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

                            # Date Range (RangeSlider + inputs)
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
                                    for i in range(0, len(unique_dates), 50)
                                },
                                tooltip={"placement": "bottom", "always_visible": True},
                            ),

                            html.P("Filter by shark species:"),
                            # MULTIPLE SELECTION HERE
                            dcc.Dropdown(
                                id="species-dropdown",
                                options=species_options,
                                placeholder="Select Shark Species",
                                multi=True,  # <<<<------
                            ),
                        ],
                    ),

                    # Right Column (Map + 2 Charts)
                    html.Div(
                        className="eight columns div-for-charts bg-grey",
                        style={
                            "display": "flex",
                            "flexDirection": "column",
                            "height": "100vh",
                            "padding": "10px",
                            "overflowY": "auto",
                        },
                        children=[
                            # Map: ~ top 50%
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
                            # Pie chart + second chart side by side
                            html.Div(
                                style={
                                    "flex": "0 0 50%",
                                    "marginTop": "5px",
                                    "display": "flex",
                                    "flexDirection": "row",
                                    "justifyContent": "space-between",
                                },
                                children=[
                                    # Pie chart
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
                                    # Placeholder second chart
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

    dcc.Store(id="selected-incidents-store", data={"rows": [], "current_index": 0}),

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
# 1) Sync RangeSlider & Start/End Inputs
# ------------------------------------------------------------------------------
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

    start_idx, end_idx = slider_range

    try:
        start_idx = date_to_index[pd.to_datetime(start_date)]
    except Exception:
        start_date = index_to_date[start_idx].strftime("%Y-%m-%d")

    try:
        end_idx = date_to_index[pd.to_datetime(end_date)]
    except Exception:
        end_date = index_to_date[end_idx].strftime("%Y-%m-%d")

    # Ensure in bounds
    start_idx = max(0, min(start_idx, len(unique_dates) - 1))
    end_idx = max(0, min(end_idx, len(unique_dates) - 1))

    # If reversed, swap
    if start_idx > end_idx:
        start_idx, end_idx = end_idx, start_idx

    # Final date strings
    start_date = index_to_date[start_idx].strftime("%Y-%m-%d")
    end_date = index_to_date[end_idx].strftime("%Y-%m-%d")

    return start_date, end_date, [start_idx, end_idx]


# ------------------------------------------------------------------------------
# 2) Update Map based on RangeSlider & Multi-Species
# ------------------------------------------------------------------------------
@app.callback(
    Output("map-graph", "figure"),
    [Input("date-slider", "value"),
     Input("species-dropdown", "value")]
)
def update_map(slider_range, selected_species):
    """
    slider_range is [start_idx, end_idx]
    selected_species can be a list of species or None.
    """
    if not slider_range:
        filtered_df = df.copy()
    else:
        start_date = index_to_date[slider_range[0]]
        end_date = index_to_date[slider_range[1]]
        filtered_df = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)]

    if selected_species:
        # For multiple species, we filter via .isin(list_of_species)
        filtered_df = filtered_df[filtered_df["Shark.common.name"].isin(selected_species)]

    if filtered_df.empty:
        return px.scatter_mapbox(
            pd.DataFrame({"Latitude": [], "Longitude": [], "Incident Count": []}),
            lat="Latitude", lon="Longitude", size="Incident Count",
            zoom=4, center={"lat": -25.0, "lon": 133.0},
            mapbox_style="open-street-map"
        )

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
# 3) Modal + Blur Logic (unchanged)
# ------------------------------------------------------------------------------
@app.callback(
    Output("info-modal", "style"),
    Output("selected-incidents-store", "data"),
    Output("modal-incident-content", "children"),
    Output("prev-incident", "style"),
    Output("next-incident", "style"),
    Output("background-container", "className"),
    [
        Input("date-slider", "value"),
        Input("species-dropdown", "value"),
        Input("map-graph", "clickData"),
        Input("close-modal", "n_clicks"),
        Input("prev-incident", "n_clicks"),
        Input("next-incident", "n_clicks"),
    ],
    [State("selected-incidents-store", "data")]
)
def handle_modal_and_incidents(
    slider_range, selectedSpecies, clickData,
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

    # Filter by slider
    if slider_range:
        start_date = index_to_date[slider_range[0]]
        end_date = index_to_date[slider_range[1]]
        filter_df = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)]
    else:
        filter_df = df.copy()

    # Filter by multi-species
    if selectedSpecies:
        filter_df = filter_df[filter_df["Shark.common.name"].isin(selectedSpecies)]

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
# Helpers for Modal
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
# 4) Box-select => Update Pie Chart
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