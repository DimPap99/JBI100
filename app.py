import dash
from dash import dcc, html
import pandas as pd
from dash.dependencies import Input, Output, State
import plotly.express as px
from datetime import datetime as dt
from dash.exceptions import PreventUpdate

# Initialize the Dash app
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

# Construct a single 'Date' column
df["Date"] = pd.to_datetime(
    df["Incident.year"].astype(str) + "-" + df["Incident.month"].astype(str),
    errors="coerce"
)

# Additional columns
df["Month"] = df["Date"].dt.month_name()
df["DayOfWeek"] = df["Date"].dt.day_name()

df = df.sort_values("Date")
unique_dates = df["Date"].dropna().unique()
date_to_index = {date: i for i, date in enumerate(unique_dates)}
index_to_date = {i: date for i, date in enumerate(unique_dates)}

# Convert numeric columns
df["Shark.length.m"] = pd.to_numeric(df.get("Shark.length.m"), errors="coerce")
df["Depth.of.incident.m"] = pd.to_numeric(df.get("Depth.of.incident.m"), errors="coerce")
df["Distance.to.shore.m"] = pd.to_numeric(df.get("Distance.to.shore.m"), errors="coerce")
df["Water.visability.m"] = pd.to_numeric(df.get("Water.visability.m"), errors="coerce")
df["Air.temperature.°C"] = pd.to_numeric(df.get("Air.temperature.°C"), errors="coerce")

# Victim age
df["Victim.age"] = pd.to_numeric(df.get("Victim.age"), errors="coerce")

# Custom month and day order for dropdown
custom_month_order = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

custom_day_order = [
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
]

# State filter
state_options = [
    {"label": st, "value": st}
    for st in sorted(df["State"].dropna().unique())
]
# Build the list of dropdown options
species_options = [
    {"label": s, "value": s}
    for s in df["Shark.common.name"].dropna().unique()
]
month_options = [
    {"label": m, "value": m}
    for m in custom_month_order
    if m in df["Month"].dropna().unique()
]
dayofweek_options = [
    {"label": d, "value": d}
    for d in custom_day_order
    if d in df["DayOfWeek"].dropna().unique()
]
victim_activity_options = [
    {"label": act, "value": act}
    for act in df["Victim.activity"].dropna().unique()
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

# Define colorblind-friendly and default palettes
CB_COLOR_CYCLE = [
    '#377eb8', '#ff7f00', '#4daf4a',
    '#f781bf', '#a65628', '#984ea3',
    '#999999', '#e41a1c', '#dede00'
]

DEFAULT_COLOR_CYCLE = px.colors.qualitative.Plotly  # Default Plotly palette

def get_color_discrete_sequence(colorblind_active):
    """
    Return the appropriate color_discrete_sequence based on the colorblind mode.
    """
    return CB_COLOR_CYCLE if colorblind_active else DEFAULT_COLOR_CYCLE

# ------------------------------------------------------------------------------
# App Layout
# ------------------------------------------------------------------------------
app.layout = html.Div(style={"position": "relative"}, children=[

    # (1) New Button & Store for toggling colorblind mode
    html.Div(
    [
        html.Button(
            "Toggle Colorblind Mode",
            id="toggle-colorblind-button",
            n_clicks=0,
            style={
                "zIndex": 9999
            }
        ),
        html.Button(
            "Help",
            id="help-button",
            n_clicks=0,
            style={
                "zIndex": 9999
            }
        )
    ],
    style={
        "position": "absolute",
        "top": "10px",
        "left": "10px",
        "display": "flex",
        "alignItems": "center"
        }
    ),

   

    html.Div(
        id="background-container",
        children=[
            html.Div(
                className="row",
                children=[
                    # Left Column (Controls + Third Chart)
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
                                html.Button(
                                    "Apply",
                                    id="apply-date-button",
                                    n_clicks=0,
                                    style={"marginLeft": "10px"}
                                ),
                                html.Button(
                                    "Reset",
                                    id="reset-button",
                                    n_clicks=0,
                                    style={"marginLeft": "10px"}
                                ),
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

                                # New className (default is "blue-slider" in normal mode)
                                className="blue-slider"
                            ),
                            html.P("Filters:"),
                            dcc.Dropdown(
                                id="state-dropdown",
                                options=state_options,
                                placeholder="Select State(s)",
                                multi=True,
                                style={"marginBottom": "10px"}
                            ),

                            dcc.Dropdown(
                                id="species-dropdown",
                                options=species_options,
                                placeholder="Select Shark Species",
                                multi=True,
                                style={"marginBottom": "10px"}
                            ),
                            dcc.Dropdown(
                                id="month-dropdown",
                                options=month_options,
                                placeholder="Select Month(s)",
                                multi=True,
                                style={"marginBottom": "10px"}
                            ),
                            dcc.Dropdown(
                                id="dayofweek-dropdown",
                                options=dayofweek_options,
                                placeholder="Select Day(s)",
                                multi=True,
                                style={"marginBottom": "10px"}
                            ),
                            dcc.Dropdown(
                                id="victim-activity-dropdown",
                                options=victim_activity_options,
                                placeholder="Select Victim Activity",
                                multi=True
                            ),

                            # Third Chart (Histogram) below the Filters
                            html.Div(
                                style={
                                    "marginTop": "20px",
                                    "height": "auto",
                                    "backgroundColor": "#F3F3F3",
                                    "padding": "10px"
                                },
                                children=[
                                    html.H4("Histogram", style={"paddingLeft": "12px"}),

                                    dcc.RadioItems(
                                        id="histogram-type",
                                        options=[
                                            {"label": "Victim Age", "value": "age"},
                                            {"label": "State", "value": "state"},
                                            {"label": "Month", "value": "month"},
                                            {"label": "Day of Week", "value": "dayofweek"}
                                        ],
                                        value="age",  # Default
                                        inline=True,
                                        style={"marginBottom": "15px"}
                                    ),

                                     html.Button(
                                        "Clear Selection",
                                        id="clear-histogram-selection",
                                        n_clicks=0,
                                        style={"marginBottom": "15px"}
                                        ),

                                    dcc.Graph(
                                        id="third-chart",
                                        style={"height": "85%", "width": "100%"},
                                        config={"displayModeBar": False},
                                    )
                                ]
                            ),
                        ],
                    ),

                    # Right Column (Map + Treemap + PCP)
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
                            # Map: top 50%
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
                            # Treemap + PCP side by side
                            html.Div(
                                style={
                                    "flex": "0 0 50%",
                                    "marginTop": "5px",
                                    "display": "flex",
                                    "flexDirection": "row",
                                    "justifyContent": "space-between",
                                },
                                children=[
                                    html.Div(
                                        style={"flex": "1", "marginRight": "5px"},
                                        children=[
                                            html.H4(
                                                "Box-Selected Data (Treemap)",
                                                style={"paddingLeft": "12px"}
                                            ),
                                            dcc.Graph(
                                                id="pie-chart",
                                                style={"height": "85%", "width": "100%"}
                                            )
                                        ]
                                    ),
                                    html.Div(
                                        style={"flex": "1", "marginLeft": "5px"},
                                        children=[
                                            html.H4("Parallel Coordinates Plot", style={"paddingLeft": "12px"}),
                                            dcc.Graph(
                                                id="pcp-graph",
                                                style={"height": "85%", "width": "100%"}
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

    # --------------------------------------------------------------------------
    # Stores
    # --------------------------------------------------------------------------
    dcc.Store(id="selected-incidents-store", data={"rows": [], "current_index": 0}),
    dcc.Store(id="filtered-data-store"),
    dcc.Store(id="pie-selected-species", data=None),
    dcc.Store(id="histogram-click-store", data=None),
    dcc.Store(id="colorblind-store", data=False),
    dcc.Store(id="selected-bins", data={"hist_type": "age", "values": []}  # or whatever initial structure you prefer
),

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
    html.Div(
    id="help-modal",
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
        "color": "black",
    },
    children=[
        html.Button(
            "Close",
            id="close-help-modal",
            style={"float": "right", "margin": "10px"}
        ),
        html.Div(
            children=[
                html.H4("How to Use This Tool"),
                html.P(
                    "Welcome! This dashboard provides an interactive interface for "
                    "exploring shark incident data in Australia. Below are some pointers "
                    "on how to navigate and filter the data:"
                ),
                html.Ul([
                    html.Li(
                        "Use the date filters and slider to narrow down incidents within a specific time range."
                    ),
                    html.Li(
                        "Select states, shark species, months, or days of the week from the dropdowns to refine your search."
                    ),
                    html.Li(
                        "Click on a bar in the histogram to see details for that category. "
                        "You can also clear or reset these selections at any time."
                    ),
                    html.Li(
                        "Use the map to explore incidents geographically. "
                        "Zoom, pan, or click on a point to see more information about a specific incident."
                    ),
                    html.Li(
                        "Box-select (click and drag) on the map or treemap to isolate specific points or categories."
                    ),
                    html.Li(
                        "Open the modal window by clicking on a map point, then use 'Previous' and 'Next' to cycle through incidents."
                    ),
                    html.Li(
                        "If you have color vision difficulties, you can toggle the Colorblind Mode at the top-left."
                    ),
                    html.Li(
                        "Use the Parallel Coordinates Plot to compare numeric variables (e.g., shark length, water depth) across incidents."
                    ),
                ]),
                html.P(
                    "Feel free to experiment with the filters in any order to discover trends in the data. "
                    "Click 'Close' to exit this help modal."
                ),
            ],
            style={"color": "black"},
            ),
        ],
    ),
]),

# Add a help modal
    

# ------------------------------------------------------------------------------
# (A) NEW CALLBACK: Toggle the colorblind-store
# ------------------------------------------------------------------------------
@app.callback(
    Output("colorblind-store", "data"),
    Input("toggle-colorblind-button", "n_clicks"),
    State("colorblind-store", "data"),
    prevent_initial_call=True
)
def toggle_colorblind_mode(n_clicks, current_value):
    """
    Simply flip the boolean in colorblind-store each time the button is clicked.
    """
    return not current_value

# ------------------------------------------------------------------------------
# colorblind year slider
# ------------------------------------------------------------------------------
@app.callback(
    Output("date-slider", "className"),
    Input("colorblind-store", "data")
)
def update_slider_classname(colorblind_active):
    """
    Toggle the slider's CSS class.
    If colorblind_active=True, assign 'grey-slider';
    otherwise 'blue-slider'.
    """
    return "grey-slider" if colorblind_active else "blue-slider"

# ------------------------------------------------------------------------------
# 1) Single Callback to Handle "Apply" AND "Reset"  (Unchanged)
# ------------------------------------------------------------------------------
@app.callback(
    [
        Output("start-date-input", "value"),
        Output("end-date-input", "value"),
        Output("date-slider", "value"),
        Output("species-dropdown", "value"),
        Output("map-graph", "selectedData"),
        Output("month-dropdown", "value"),
        Output("dayofweek-dropdown", "value"),
        Output("victim-activity-dropdown", "value"),
        Output("state-dropdown", "value"),
        Output("histogram-click-store", "data", allow_duplicate=True),
    ],
    [
        Input("apply-date-button", "n_clicks"),
        Input("reset-button", "n_clicks"),
    ],
    [
        State("start-date-input", "value"),
        State("end-date-input", "value"),
        State("date-slider", "value"),
    ],
    prevent_initial_call=True
)
def apply_or_reset(
    apply_clicks, reset_clicks,
    current_start_date, current_end_date, current_slider
):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate

    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if triggered_id == "apply-date-button":
        try:
            start_idx = date_to_index[pd.to_datetime(current_start_date)]
        except Exception:
            start_idx = current_slider[0]
            current_start_date = index_to_date[start_idx].strftime("%Y-%m-%d")

        try:
            end_idx = date_to_index[pd.to_datetime(current_end_date)]
        except Exception:
            end_idx = current_slider[1]
            current_end_date = index_to_date[end_idx].strftime("%Y-%m-%d")

        start_idx = max(0, min(start_idx, len(unique_dates) - 1))
        end_idx = max(0, min(end_idx, len(unique_dates) - 1))

        if start_idx > end_idx:
            start_idx, end_idx = end_idx, start_idx

        new_start_date = index_to_date[start_idx].strftime("%Y-%m-%d")
        new_end_date = index_to_date[end_idx].strftime("%Y-%m-%d")
        new_slider = [start_idx, end_idx]

        return (
            new_start_date,
            new_end_date,
            new_slider,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
        )

    elif triggered_id == "reset-button":
        default_start = str(unique_dates[0].date())
        default_end = str(unique_dates[-1].date())
        default_slider_range = [0, len(unique_dates) - 1]

        return (
            default_start,
            default_end,
            default_slider_range,
            [],
            None,
            [],
            [],
            [],
            [],
            None
        )

    raise PreventUpdate


# ------------------------------------------------------------------------------
# 2) COMBINED callback for treemap-click + reset => set pie-selected-species (Unchanged)
# ------------------------------------------------------------------------------
@app.callback(
    Output("pie-selected-species", "data"),
    [
        Input("pie-chart", "clickData"),
        Input("reset-button", "n_clicks"),
    ],
    prevent_initial_call=True
)
def handle_treemap_click_and_reset(treemap_click, reset_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate

    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if triggered_id == "pie-chart":
        if treemap_click and "points" in treemap_click:
            points = treemap_click["points"]
            if points:
                return points[0].get("id")
        return dash.no_update

    elif triggered_id == "reset-button":
        return None

    raise PreventUpdate


# ------------------------------------------------------------------------------
# (2) CALLBACK FOR HISTOGRAM CLICK => Store selected 'Victim.age' 
# ------------------------------------------------------------------------------
# @app.callback(
#     Output("histogram-click-store", "data"),
#     [
#         Input("third-chart", "clickData"),
#         Input("reset-button", "n_clicks")
#     ],
#     [State("histogram-type", "value")],
#     prevent_initial_call=True
# )
# def handle_histogram_click(click_data, reset_clicks, histogram_type):
    
#     ctx = dash.callback_context
#     if not ctx.triggered:
#         raise PreventUpdate

#     triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

#     if triggered_id == "third-chart" and click_data:
#         clicked_value = click_data["points"][0].get("x")
#         return {"type": histogram_type, "value": clicked_value}

#     elif triggered_id == "reset-button":
#         return None

#     raise PreventUpdate


# ------------------------------------------------------------------------------
# 3) “Master” Filtering Callback (including NEW State filter & histogram click)
# ------------------------------------------------------------------------------
@app.callback(
    Output("filtered-data-store", "data"),
    [
        Input("date-slider", "value"),
        Input("state-dropdown", "value"),
        Input("species-dropdown", "value"),
        Input("map-graph", "selectedData"),
        Input("month-dropdown", "value"),
        Input("dayofweek-dropdown", "value"),
        Input("victim-activity-dropdown", "value"),
        Input("selected-bins", "data"),
    ]
)
def update_filtered_data_store(
    slider_range, selected_states, selected_species,
    map_selected, selected_months, selected_dows,
    selected_activities, selected_bins
):
    
    filtered_df_local = df.copy()

    # 1) Filter by date
    if slider_range:
        start_date = index_to_date[slider_range[0]]
        end_date = index_to_date[slider_range[1]]
        filtered_df_local = filtered_df_local[
            (filtered_df_local["Date"] >= start_date) &
            (filtered_df_local["Date"] <= end_date)
        ]

    # 2) Other filters: state, species, month, day-of-week, victim activity
    if selected_states:
        filtered_df_local = filtered_df_local[filtered_df_local["State"].isin(selected_states)]
    if selected_species:
        filtered_df_local = filtered_df_local[filtered_df_local["Shark.common.name"].isin(selected_species)]
    if selected_months:
        filtered_df_local = filtered_df_local[filtered_df_local["Month"].isin(selected_months)]
    if selected_dows:
        filtered_df_local = filtered_df_local[filtered_df_local["DayOfWeek"].isin(selected_dows)]
    if selected_activities:
        filtered_df_local = filtered_df_local[filtered_df_local["Victim.activity"].isin(selected_activities)]

    # 3) NEW: Multi-bin filtering from `selected-bins`
    #    `selected_bins` is a dict like: { "hist_type": "age", "values": [23, 30, 35] }
    hist_type = selected_bins["hist_type"] if selected_bins else None
    bin_list  = selected_bins["values"] if selected_bins else []

    if hist_type and bin_list:
        if hist_type == "age":
            # numeric match for Victim.age
            filtered_df_local = filtered_df_local[filtered_df_local["Victim.age"].isin(bin_list)]
        elif hist_type == "state":
            filtered_df_local = filtered_df_local[filtered_df_local["State"].isin(bin_list)]
        elif hist_type == "month":
            filtered_df_local = filtered_df_local[filtered_df_local["Month"].isin(bin_list)]
        elif hist_type == "dayofweek":
            filtered_df_local = filtered_df_local[filtered_df_local["DayOfWeek"].isin(bin_list)]

    return filtered_df_local.to_dict("records")

@app.callback(
    Output("filtered-data-store", "data", allow_duplicate=True),
    [
        Input("map-graph", "selectedData"),
        State("filtered-data-store", "data"),
    ],
    prevent_initial_call=True,
)
def update_data_on_map_selection(selected_data, current_data):
    """
    Update the filtered data store based on box selection on the map.
    """
    if not selected_data:
        # If no selection is made, return the current data
        raise PreventUpdate

    # Extract the selected points (lat/lon) from the map
    selected_points = selected_data.get("points", [])
    if not selected_points:
        raise PreventUpdate

    selected_coords = [
        (round(point["lat"], 5), round(point["lon"], 5)) for point in selected_points
    ]

    # Convert current_data to DataFrame for filtering
    filtered_df = pd.DataFrame(current_data)

    # Filter rows matching selected coordinates
    filtered_df = filtered_df[
        filtered_df.apply(
            lambda row: (row["Latitude"], row["Longitude"]) in selected_coords, axis=1
        )
    ]

    return filtered_df.to_dict("records")

# ------------------------------------------------------------------------------
# 4) Build Treemap from filtered data
#  
# ------------------------------------------------------------------------------
@app.callback(
    Output("pie-chart", "figure"),
    [
        Input("filtered-data-store", "data"),
        Input("colorblind-store", "data") ,
    ]
)
def update_treemap_from_filtered_data(filtered_data, colorblind_active):
    if not filtered_data:
        empty_df = pd.DataFrame({
            "Shark.common.name": [], "Victim.injury": [], "Provoked/unprovoked": [], "Count": []
        })
        fig = px.treemap(
            empty_df,
            path=["Shark.common.name", "Victim.injury", "Provoked/unprovoked"],
            values="Count",
            title="No Data"
        )
        fig.update_layout(clickmode='event+select')
        return fig

    filtered_df_local = pd.DataFrame(filtered_data)
    if filtered_df_local.empty:
        empty_df = pd.DataFrame({
            "Shark.common.name": [], "Victim.injury": [], "Provoked/unprovoked": [], "Count": []
        })
        fig = px.treemap(
            empty_df,
            path=["Shark.common.name", "Victim.injury", "Provoked/unprovoked"],
            values="Count",
            title="No Data"
        )
        fig.update_layout(clickmode='event+select')
        return fig

    tree_data = (
        filtered_df_local
        .groupby(["Shark.common.name", "Victim.injury", "Provoked/unprovoked"])
        .size()
        .reset_index(name="Count")
    )

    # Use the global color sequence function
    color_discrete_sequence = get_color_discrete_sequence(colorblind_active)

    # Create the treemap
    fig = px.treemap(
        tree_data,
        path=["Shark.common.name", "Victim.injury", "Provoked/unprovoked"],
        values="Count",
        title="Shark Incidents Treemap (Species -> Injury -> Provoked)",
        color="Shark.common.name",
        color_discrete_sequence=color_discrete_sequence
    )
    fig.update_layout(
        dragmode="select",  # Enable box selection
        margin={"r": 0, "t": 40, "l": 0, "b": 0},)
        # clickmode='event+select')
    return fig


# ------------------------------------------------------------------------------
# 5) Update Map to highlight the treemap-clicked path

# ------------------------------------------------------------------------------
# 5) Update Map to highlight the treemap-clicked path
# (Now includes colorblind-store as Input)

@app.callback(
    Output("map-graph", "figure"),
    [
        Input("filtered-data-store", "data"),
        Input("pie-selected-species", "data"),
        Input("colorblind-store", "data")  # NEW input
    ]
)
def update_map_from_filtered_data_and_treemap_path(filtered_data, treemap_path, colorblind_active):
    # Colorblind-friendly color cycle
    # 1) If no data, return empty figure
    if not filtered_data:
        return px.scatter_mapbox(
            pd.DataFrame({"Latitude": [], "Longitude": [], "Incident Count": []}),
            lat="Latitude",
            lon="Longitude",
            size="Incident Count",
            zoom=4,
            center={"lat": -25.0, "lon": 133.0},
            mapbox_style="open-street-map",
            title="No Data"
        )

    df_local = pd.DataFrame(filtered_data)
    if df_local.empty:
        return px.scatter_mapbox(
            pd.DataFrame({"Latitude": [], "Longitude": [], "Incident Count": []}),
            lat="Latitude",
            lon="Longitude",
            size="Incident Count",
            zoom=4,
            center={"lat": -25.0, "lon": 133.0},
            mapbox_style="open-street-map",
            title="No Data"
        )

    # 2) Highlight "Selected" vs. "Other", same as before
    df_local["Highlight"] = "Other"
    if treemap_path:
        path_parts = treemap_path.split("/")
        species_sel = path_parts[0] if len(path_parts) >= 1 else None
        injury_sel = path_parts[1] if len(path_parts) >= 2 else None
        provoked_sel = path_parts[2] if len(path_parts) >= 3 else None

        mask = pd.Series([True]*len(df_local))
        if species_sel:
            mask &= (df_local["Shark.common.name"] == species_sel)
        if injury_sel:
            mask &= (df_local["Victim.injury"] == injury_sel)
        if provoked_sel:
            mask &= (df_local["Provoked/unprovoked"] == provoked_sel)

        df_local.loc[mask, "Highlight"] = "Selected"

    bubble_data = (
        df_local.groupby(["Latitude", "Longitude", "Highlight"])
        .size()
        .reset_index(name="Count")
    )

    # 3) Switch color scales based on colorblind_active
    #    - If colorblind mode is ON, use a colorblind-friendly scale
    #    - If colorblind mode is OFF, keep the original "blue -> red" 
    color_discrete_sequence = get_color_discrete_sequence(colorblind_active)

    # 4) Build the figure
    fig = px.scatter_mapbox(
        bubble_data,
        lat="Latitude",
        lon="Longitude",
        size="Count",
        hover_name="Count",
        color="Highlight",
        zoom=4,
        center={"lat": -25.0, "lon": 133.0},
        mapbox_style="open-street-map",  # original
        color_discrete_sequence = color_discrete_sequence,

    )

    # Keep your original marker opacity
    fig.update_traces(marker=dict(opacity=0.6), selector=dict(mode='markers'))

    fig.update_layout(
        # title="Shark Incidents Density",
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
        dragmode="select"
    )

    return fig


# ------------------------------------------------------------------------------
# 6) Modal + Blur Logic
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

    default_style = {"display": "none"}
    default_store = {"rows": [], "current_index": 0}
    default_content = html.Div("No incident data available")
    no_blur = ""
    blurred = "blurred"

    prev_style = {"marginRight": "20px", "padding": "8px 16px"}
    next_style = {"padding": "8px 16px"}

    if "close-modal" in triggered_id:
        return default_style, default_store, default_content, prev_style, next_style, no_blur

    if slider_range:
        start_date = index_to_date[slider_range[0]]
        end_date = index_to_date[slider_range[1]]
        filter_df = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)]
    else:
        filter_df = df.copy()

    if selectedSpecies:
        filter_df = filter_df[filter_df["Shark.common.name"].isin(selectedSpecies)]

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
# 7) Third Chart (Histogram):  
# ------------------------------------------------------------------------------
@app.callback(
    Output("third-chart", "figure"),
    [
        Input("filtered-data-store", "data"),
        Input("pie-selected-species", "data"),
        Input("histogram-type", "value"),
        Input("colorblind-store", "data")  # colorblind option
    ]
)
def update_histogram(filtered_data, treemap_path, histogram_type, colorblind_active):
    if not filtered_data:
        return px.scatter(title="No Data in Histogram")

    df_local = pd.DataFrame(filtered_data)
    if df_local.empty:
        return px.scatter(title="No Data in Histogram")

    if treemap_path:
        path_parts = treemap_path.split("/")
        species_sel = path_parts[0] if len(path_parts) >= 1 else None
        injury_sel = path_parts[1] if len(path_parts) >= 2 else None
        provoked_sel = path_parts[2] if len(path_parts) >= 3 else None

        mask = pd.Series([True] * len(df_local))
        if species_sel:
            mask &= (df_local["Shark.common.name"] == species_sel)
        if injury_sel:
            mask &= (df_local["Victim.injury"] == injury_sel)
        if provoked_sel:
            mask &= (df_local["Provoked/unprovoked"] == provoked_sel)
        df_local = df_local[mask]

    if histogram_type == "age":
        df_local["Victim.age"] = pd.to_numeric(df_local["Victim.age"], errors="coerce")
        df_local = df_local.dropna(subset=["Victim.age"])
        x_axis = "Victim.age"
        title = "Histogram: Victim Age"
    elif histogram_type == "dayofweek":
        df_local = df_local.dropna(subset=["DayOfWeek"])
        x_axis = "DayOfWeek"
        title = "Histogram: Day of Week"
    elif histogram_type == "state":
        df_local = df_local.dropna(subset=["State"])
        x_axis = "State"
        title = "Histogram: State"
    elif histogram_type == "month":
        df_local = df_local.dropna(subset=["Month"])
        x_axis = "Month"
        title = "Histogram: Month"
    else:
        return px.scatter(title="Invalid Histogram Type")

    fig = px.histogram(
        df_local,
        x=x_axis,
        category_orders={"DayOfWeek": custom_day_order, "Month": custom_month_order},
        title=title
    )

    # Choose color palette
    if colorblind_active:
        fig.update_traces(marker_color="#3B528B")  # example colorblind-friendly
    else:
        fig.update_traces(marker_color="#636EFA")  # Plotly default

    fig.update_layout(
        clickmode="event+select",
        margin={"r": 0, "t": 40, "l": 0, "b": 0}
    )
    return fig


# ------------------------------------------------------------------------------
# 8) PCP: (B) ADD colorblind-store as Input
# ------------------------------------------------------------------------------
@app.callback(
    Output("pcp-graph", "figure"),
    [
        Input("filtered-data-store", "data"),
        Input("pie-selected-species", "data"),
        Input("colorblind-store", "data")  # NEW
    ]
)
def update_pcp_graph_no_grouping(filtered_data, treemap_path, colorblind_active):
    if not filtered_data:
        return px.scatter(title="No Data in PCP")

    df_local = pd.DataFrame(filtered_data)
    if df_local.empty:
        return px.scatter(title="No Data in PCP")

    if treemap_path:
        path_parts = treemap_path.split("/")
        species_sel = path_parts[0] if len(path_parts) >= 1 else None
        injury_sel = path_parts[1] if len(path_parts) >= 2 else None
        provoked_sel = path_parts[2] if len(path_parts) >= 3 else None

        mask = pd.Series([True]*len(df_local))
        if species_sel:
            mask &= (df_local["Shark.common.name"] == species_sel)
        if injury_sel:
            mask &= (df_local["Victim.injury"] == injury_sel)
        if provoked_sel:
            mask &= (df_local["Provoked/unprovoked"] == provoked_sel)
        df_local = df_local[mask]

    numeric_cols = [
        "Shark.length.m",
        "Depth.of.incident.m",
        "Distance.to.shore.m",
        "Water.visability.m",
        "Air.temperature.°C"
    ]
    for c in numeric_cols:
        df_local[c] = pd.to_numeric(df_local[c], errors="coerce")

    df_local = df_local.dropna(subset=numeric_cols)
    if df_local.empty:
        return px.scatter(title="No Data for PCP")

    fig = px.parallel_coordinates(
        df_local,
        dimensions=numeric_cols,
        labels={
            "Shark.length.m": "Shark Length (m)",
            "Depth.of.incident.m": "Depth (m)",
            "Distance.to.shore.m": "Shore Dist (m)",
            "Water.visability.m": "Visibility (m)",
            "Air.temperature.°C": "Air Temp (°C)"
        }
    )

    if colorblind_active:
        # example color that stands out well for colorblind
        fig.update_traces(line_color="#3B528B")
    else:
        # original color
        fig.update_traces(line_color="blue")

    fig.update_layout(title="")
    return fig

# ------------------------------------------------------------------------------
# 9) Help Modal
# ------------------------------------------------------------------------------
@app.callback(
    [
        Output("help-modal", "style", allow_duplicate=True),
        Output("background-container", "className", allow_duplicate=True),
    ],
    [
        Input("help-button", "n_clicks"),
        Input("close-help-modal", "n_clicks"),
    ],
    prevent_initial_call=True
)
def toggle_help_modal(help_clicks, close_help_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
    # Show modal when the Help button is clicked
    if triggered_id == "help-button":
        return (
            {
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
            },
            "blurred",
        )
    # Hide modal when the Close button is clicked
    if triggered_id == "close-help-modal":
        return {"display": "none"}, ""
    raise PreventUpdate

# ------------------------------------------------------------------------------
# 10) Clear Histogram Selection
# ------------------------------------------------------------------------------
# -------------------------------------------------------
# NEW CALLBACK: Toggle bins in "selected-bins" via clicks
# -------------------------------------------------------
@app.callback(
    Output("selected-bins", "data"),
    Input("third-chart", "clickData"),
    [
        State("selected-bins", "data"),
        State("histogram-type", "value"),
    ],
    prevent_initial_call=True
)
def accumulate_histogram_bins(click_data, store_data, current_hist_type):
    """
    Each click on a histogram bin will toggle that bin in store_data["values"].
    We also store the histogram type so we know which dimension is being selected.
    """
    if not click_data:
        raise PreventUpdate

    bin_clicked = click_data["points"][0].get("x")
    if store_data is None:
        store_data = {"hist_type": current_hist_type, "values": []}

    # If user switched histogram type (age -> month, etc.), reset old selections
    if store_data["hist_type"] != current_hist_type:
        store_data = {"hist_type": current_hist_type, "values": []}

    # Toggle logic
    if bin_clicked in store_data["values"]:
        # If bin is already selected, remove it
        store_data["values"].remove(bin_clicked)
    else:
        # Otherwise add it
        store_data["values"].append(bin_clicked)

    return store_data

# -------------------------------------------------------
# Clear Histogram Selection
# -------------------------------------------------------
@app.callback(
    [
        Output("selected-bins", "data", allow_duplicate=True),
        Output("third-chart", "clickData", allow_duplicate=True),
    ],
    Input("clear-histogram-selection", "n_clicks"),
    prevent_initial_call=True
)
def clear_multi_histogram_selection(n_clicks):
    """
    Reset both the selected-bins store and the histogram's own clickData
    whenever the user clicks the 'Clear Selection' button.
    """
    if n_clicks:
        empty_store = {"hist_type": None, "values": []}
        return empty_store, None
    raise PreventUpdate

# ------------------------------------------------------------------------------
# Run
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    app.run_server(debug=True)
