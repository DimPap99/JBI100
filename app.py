import dash
from dash import dcc, html
import pandas as pd
from dash.dependencies import Input, Output, State
import plotly.express as px
from datetime import datetime as dt
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go

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

# Reconstruct 'Date' column from year-month data
df["Date"] = pd.to_datetime(
    df["Incident.year"].astype(str) + "-" + df["Incident.month"].astype(str),
    errors="coerce"
)

# New columns for better filtering and grouping
df["Month"] = df["Date"].dt.month_name()
df["DayOfWeek"] = df["Date"].dt.day_name()

# Sorting 'Date' values
df = df.sort_values("Date")

# Store unique dates and create mappings to indices
unique_dates = df["Date"].dropna().unique()
date_to_index = {date: i for i, date in enumerate(unique_dates)}
index_to_date = {i: date for i, date in enumerate(unique_dates)}

# Convert 'Site.category' to title case
df["Site.category"] = df["Site.category"].str.title()

# Create numeric codes for Victim.injury
# eplacing values in Victim.injury column where it is needed
df["Victim.injury"] = df["Victim.injury"].str.replace(r"(Injured|injury)", "injured", case=False, regex=True)
# Drop the unkown category
df = df[df["Victim.injury"] != "unknown"]
# Custom mapping for injury type
injury_map = {
    "uninjured": 0,
    "injured": 1,
    "fatal": 2
}
df["Victim.injury.num"] = df["Victim.injury"].map(injury_map)
# Replacing values in 'Victim.activity' column where it is needed
df['Victim.activity'] = df['Victim.activity'].str.replace("snorkeling", "snorkelling")
df['Victim.activity'] = df['Victim.activity'].str.replace("diving, collecting", "diving")

# Convert certain columns to numeric, ignoring errors
df["Shark.length.m"] = pd.to_numeric(df.get("Shark.length.m"), errors="coerce")
df["Depth.of.incident.m"] = pd.to_numeric(df.get("Depth.of.incident.m"), errors="coerce")
df["Distance.to.shore.m"] = pd.to_numeric(df.get("Distance.to.shore.m"), errors="coerce")
df["Water.visability.m"] = pd.to_numeric(df.get("Water.visability.m"), errors="coerce")
df["Air.temperature.°C"] = pd.to_numeric(df.get("Air.temperature.°C"), errors="coerce")
df["Total.water.depth.m"] = pd.to_numeric(df.get("Total.water.depth.m"), errors="coerce")
df["Time.in.water.min"] = pd.to_numeric(df.get("Time.in.water.min"), errors="coerce")

# Convert victim age to numeric
df["Victim.age"] = pd.to_numeric(df.get("Victim.age"), errors="coerce")

# Define bins and labels for Victim.age grouping
age_bins = [0, 4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 44, 48, 52, 56, 60, 64, 68, 72, 76, 80, 84, 88, 92, 96, 100]
age_labels = [f"{age}-{age+3}" for age in age_bins[:-1]]

# Create a new column for age group
df["Victim.age.group"] = pd.cut(df["Victim.age"], bins=age_bins, labels=age_labels, right=False)

# Define custom sorting orders for months, days, and age bins
custom_month_order = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

custom_day_order = [
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
]

custom_age_order = age_labels + ["Unknown"]

# Prepare dropdown options for filters
state_options = [
    {"label": st, "value": st}
    for st in sorted(df["State"].dropna().unique())
]
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

# Maping shark species to corresponding images
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
    """
    Returns the corresponding shark image filename based on the species name.
    If not recognized, defaults to 'unknown.webp'.
    :param species: a string variable referring to shark's species 
    :return: The image filename for the given species from the `species_image_map` dictionary.
    """
    if not species_name or not isinstance(species_name, str):
        return "unknown.webp"
    clean = species_name.strip().lower()
    return species_image_map.get(clean, "unknown.webp")

# Define colorblind-friendly and default palettes
CB_COLOR_CYCLE = [
    '#0072B2','#F0E442', '#D55E00',
    '#009E73', '#56B4E9', '#CC79A7',
    '#E69F00', '#000000'
]

DEFAULT_COLOR_CYCLE = px.colors.qualitative.G10  # Default Plotly palette

def get_color_discrete_sequence(colorblind_active):
    """
    Switching to colorblind mode
    :param colorblind_active: a boolean variable
    :return: a colorblind-friendly set of colors (CB_COLOR_CYCLE) or the default Plotly color cycle


    """
    return CB_COLOR_CYCLE if colorblind_active else DEFAULT_COLOR_CYCLE

# ------------------------------------------------------------------------------
# App Layout
# ------------------------------------------------------------------------------
app.layout = html.Div(style={"position": "relative"}, children=[

    # (1) Button & Store for toggling colorblind mode
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
                            html.H2("SharkWatch: Shark Incidents in Australia"),

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
                                className="blue-slider"  # default class for color
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
                                    html.H4("Analyze Contributing Factors", style={"paddingLeft": "12px", "color": "grey"}),

                                    # Radio buttons to choose histogram type
                                    dcc.RadioItems(
                                        id="histogram-type",
                                        options=[
                                            {"label": "Victim Age", "value": "age"},
                                            {"label": "State", "value": "state"},
                                            {"label": "Month", "value": "month"},
                                            {"label": "Day of Week", "value": "dayofweek"},
                                            {"label": "Site category", "value": "sitecategory"},
                                            {"label": "Victim activity", "value": "activity"},
                                        ],
                                        value="age",  # Default
                                        inline=True,
                                        style={"marginBottom": "15px", "color": "grey"} 
                                    ),

                                    # Buttons for applying or clearing histogram selections
                                    html.Button(
                                        "Apply Selection",
                                        id="update-histogram-button",
                                        n_clicks=0,
                                        style={"marginTop": "15px", "marginBottom": "15px"}
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

                    # Right Column (Map + Bar + PCP)
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
                            # Bar + PCP side by side
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
                                                "Shark Species Analysis",
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
                                            html.Div(
                                                style={"display": "flex", "alignItems": "center", "justifyContent": "space-between"},
                                                children=[
                                                    html.H4("Shark Profiles", style={"paddingLeft": "12px"}),
                                                ],
                                            ),
                                            dcc.Graph(
                                                id="pcp-graph",
                                                style={"height": "85%", "width": "100%"}
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
        ],
    ),

    # --------------------------------------------------------------------------
    # Stores (shared data between callbacks)
    # --------------------------------------------------------------------------
    dcc.Store(id="selected-incidents-store", data={"rows": [], "current_index": 0}),
    dcc.Store(id="filtered-data-store", data=df.to_dict("records")),
    dcc.Store(id="pie-selected-species", data=None),
    dcc.Store(id="histogram-click-store", data=None),
    dcc.Store(id="colorblind-store", data=False),
    dcc.Store(id="selected-bins", data={"hist_type": "age", "values": []}),
    dcc.Store(id="temp-bin-selection", data={"hist_type": None, "values": []}),

    # Modal to display detailed incident info
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

    # Help modal
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
                            "Use the date filters and slider to narrow down incidents within a specific time range. "
                            "Click 'Apply' to filter or 'Reset' to clear all filters."
                        ),
                        html.Li(
                            "Select states, shark species, months, days of the week, or victim activities "
                            "from the dropdowns to refine your search further."
                        ),
                        html.Li(
                            "Analyze the contributing factors using the histogram. "
                            "Switch between different data dimensions such as 'Victim Age', 'State', 'Month', "
                            "'Day of Week', 'Site Category', or 'Victim Activity' using the radio buttons."
                        ),
                        html.Li(
                            "Click on a bar in the histogram to filter other charts and graphs based on the selection. "
                            "You can toggle your selection or use the 'Clear Selection' button to reset it."
                        ),
                        html.Li(
                            "View detailed shark incident data on the map. You can zoom, pan, and select geographic regions "
                            "to analyze incidents by location. Box-select (click and drag) to isolate specific points."
                        ),
                        html.Li(
                            "The stacked bar chart shows shark species grouped by 'Provoked' or 'Unprovoked' incidents. "
                            "Only the top 10 species are shown, with the rest grouped under 'Other'."
                        ),
                        html.Li(
                            "Use the Parallel Coordinates Plot to explore numeric variables such as water depth, "
                            "distance to shore, total water depth, and time in water. The plot is color-coded based on "
                            "the type of injury for added insight. The color codings are: uninjured (0), injured (1), fatal (2)."
                        ),
                        html.Li(
                            "Enable Colorblind Mode using the 'Toggle Colorblind Mode' button at the top-left. "
                            "This updates all charts to use a colorblind-friendly palette."
                        ),
                        html.Li(
                            "Open the modal window by clicking on a point on the map, then use the 'Previous' and 'Next' "
                            "buttons to browse through incidents in detail."
                        ),
                    ]),
                    html.P(
                        "Feel free to experiment with the filters in any order to discover trends in the data. "
                        "Click 'Close' to exit this help modal."
                    ),
                ],
                style={"color": "black"},
            ),
        ]
    )
])

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
    Toggles the boolean value stored in 'colorblind-store' each time
    the 'Toggle Colorblind Mode' button is clicked.
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
    Determines the appropriate CSS class for the date slider to indicate colorblind mode.

    :param colorblind_active: A boolean indicating whether colorblind mode is enabled.
    :return: The slider's CSS class name ("grey-slider" if colorblind mode is on, "blue-slider" otherwise).
    """
    return "grey-slider" if colorblind_active else "blue-slider"

# ------------------------------------------------------------------------------
# 1) Single Callback to Handle "Apply" AND "Reset" Buttons
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
        Output("selected-bins", "data", allow_duplicate=True),
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
    """
    Manages the 'Apply' and 'Reset' buttons for date filtering.

    :param apply_clicks: Number of times the 'Apply' button has been clicked.
    :param reset_clicks: Number of times the 'Reset' button has been clicked.
    :param current_start_date: Current input for the start date (in 'YYYY-MM-DD' format).
    :param current_end_date: Current input for the end date (in 'YYYY-MM-DD' format).
    :param current_slider: Current [min, max] indices on the date slider.
    :return: A tuple that updates multiple outputs, depending on which button was triggered:
       - If 'Apply': validates the text-input date ranges and adjusts the slider accordingly.
       - If 'Reset': returns all filters to their default states.
    """
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
            dash.no_update
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
            None,
            {"hist_type": "age", "values": []}
        )

    raise PreventUpdate

# ------------------------------------------------------------------------------
# 2) Combined callback for "Treemap (Bar) click" + "Reset" => set pie-selected-species
# ------------------------------------------------------------------------------
@app.callback(
    Output("pie-selected-species", "data"),
    [
        Input("pie-chart", "clickData"),
        Input("reset-button", "n_clicks"),
    ],
    prevent_initial_call=True
)
def handle_bar_click_and_reset(bar_click, reset_clicks):
    """
    Responds to clicks on the stacked bar chart

    :param bar_click: Data from the bar chart's click event, containing details like the
                      clicked bar's species and provoked/unprovoked status.
    :param reset_clicks: Number of times the 'Reset' button has been clicked.
    :return: A string combining the clicked species and provoked/unprovoked status, or None on reset.
    """
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate

    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if triggered_id == "reset-button":
        return None

    if bar_click and "points" in bar_click:
        species_clicked = bar_click["points"][0]["customdata"][0]
        provoked_clicked = bar_click["points"][0]["customdata"][1]
        return f"{species_clicked}/{provoked_clicked}"

    return dash.no_update

# ------------------------------------------------------------------------------
# 3) “Master” Filtering Callback (includes state filter & histogram bin selection)
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
    """
    Consolidates all filter inputs 

    :param slider_range: A list of two indices [start_idx, end_idx] 
                         referencing positions in the list of unique dates.
    :param selected_states: A list of states selected from the 'state-dropdown'.
    :param selected_species: A list of shark species selected from the 'species-dropdown'.
    :param map_selected: Map selection data (not directly used here, but included for clarity).
    :param selected_months: A list of month names selected from the 'month-dropdown'.
    :param selected_dows: A list of days of the week selected from the 'dayofweek-dropdown'.
    :param selected_activities: A list of victim activities selected from the 'victim-activity-dropdown'.
    :param selected_bins: A dictionary containing the histogram filter selections, e.g. 
                         {"hist_type": "age", "values": [...]}

    :return: A list of dictionaries representing the filtered DataFrame rows.
    """
    filtered_df_local = df.copy()

    # Filter by date slider
    if slider_range:
        start_date = index_to_date[slider_range[0]]
        end_date = index_to_date[slider_range[1]]
        filtered_df_local = filtered_df_local[
            (filtered_df_local["Date"] >= start_date) &
            (filtered_df_local["Date"] <= end_date)
        ]

    # Filter by dropdowns
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

    # Apply any histogram bin filters
    hist_type = selected_bins["hist_type"] if selected_bins else None
    bin_list  = selected_bins["values"] if selected_bins else []

    if hist_type and bin_list:
        if hist_type == "age":
            filtered_df_local = filtered_df_local[filtered_df_local["Victim.age.group"].isin(bin_list)]
        elif hist_type == "state":
            filtered_df_local = filtered_df_local[filtered_df_local["State"].isin(bin_list)]
        elif hist_type == "month":
            filtered_df_local = filtered_df_local[filtered_df_local["Month"].isin(bin_list)]
        elif hist_type == "dayofweek":
            filtered_df_local = filtered_df_local[filtered_df_local["DayOfWeek"].isin(bin_list)]
        elif hist_type == "sitecategory":
            filtered_df_local = filtered_df_local[filtered_df_local["Site.category"].isin(bin_list)]
        elif hist_type == "activity":
            filtered_df_local = filtered_df_local[filtered_df_local["Victim.activity"].isin(bin_list)]

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
    Applies an additional filter based on a box or lasso selection on the map.
    Only rows matching the selected lat/long coordinates will remain.

    :param selected_data: Data representing the map selection (e.g., box/lasso).
    :param current_data: The current list of dictionaries stored in 'filtered-data-store'.
    :return: An updated list of records filtered by the selected map points.
    """
    if not selected_data:
        # If no selection is made, return the current data
        raise PreventUpdate

    selected_points = selected_data.get("points", [])
    if not selected_points:
        raise PreventUpdate

    # Round lat/lon to match the data
    selected_coords = [
        (round(point["lat"], 5), round(point["lon"], 5)) for point in selected_points
    ]

    # Convert current_data to DataFrame for filtering
    filtered_df = pd.DataFrame(current_data)

    # Keep only the rows whose lat/long is in the selected coords
    filtered_df = filtered_df[
        filtered_df.apply(
            lambda row: (row["Latitude"], row["Longitude"]) in selected_coords, axis=1
        )
    ]

    return filtered_df.to_dict("records")


@app.callback(
    Output("pie-chart", "figure"),
    [
        Input("filtered-data-store", "data"),
        Input("colorblind-store", "data"),
    ]
)
def update_stacked_bar(filtered_data, colorblind_active):
    """
    Creates a stacked bar chart showing the count of incidents by
    shark species and by provoked/unprovoked status.

    :param filtered_data: A list of dictionaries from 'filtered-data-store' representing the filtered dataset.
    :param colorblind_active: Boolean indicating whether colorblind mode is enabled.
    :return: A Plotly figure object with stacked bars for each species and provocation status.
    """
    if not filtered_data:
        fig = px.bar(title="No Data")
        fig.update_layout(clickmode='event+select')
        return fig

    filtered_df_local = pd.DataFrame(filtered_data)
    if filtered_df_local.empty:
        fig = px.bar(title="No Data")
        fig.update_layout(clickmode='event+select')
        return fig

    # Group by species and provoked/unprovoked
    bar_data = (
        filtered_df_local
        .groupby(["Shark.common.name", "Provoked/unprovoked"], as_index=False)
        .size()
        .rename(columns={"size": "Count"})
    )

    # Calculate total incidents per species
    species_totals = (
        bar_data.groupby("Shark.common.name", as_index=False)["Count"]
        .sum()
        .sort_values("Count", ascending=False)
    )

    # Keep only top N species, group others as "Other"
    max_bars = 10
    top_species = species_totals.head(max_bars)["Shark.common.name"].tolist()

    bar_data["Shark.common.name"] = bar_data["Shark.common.name"].apply(
        lambda x: x if x in top_species else "Other"
    )
    bar_data = (
        bar_data.groupby(["Shark.common.name", "Provoked/unprovoked"], as_index=False)
        .sum()
    )
    sorted_species_list = top_species + ["Other"]

    # Choose color palette (default or colorblind)
    color_discrete_sequence = get_color_discrete_sequence(colorblind_active)

    fig = px.bar(
        bar_data,
        x="Shark.common.name",
        y="Count",
        color="Provoked/unprovoked",
        barmode="stack",
        color_discrete_sequence=color_discrete_sequence,
        category_orders={"Shark.common.name": sorted_species_list},
        custom_data=["Shark.common.name", "Provoked/unprovoked"],
        title="Shark Incidents by Species and Provocation",
    )

    fig.update_layout(
        clickmode='event+select',
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
    )
    return fig


@app.callback(
    Output("map-graph", "figure"),
    [
        Input("filtered-data-store", "data"),
        Input("pie-selected-species", "data"),
        Input("colorblind-store", "data")
    ]
)
def update_map_from_filtered_data_and_treemap_path(filtered_data, treemap_path, colorblind_active):
    """
    Builds a scatter_mapbox plot showing incident counts by location.
    If a specific species/provoked combination is selected in the stacked bar,
    those points are highlighted.

    :param filtered_data: Current filtered dataset in dictionary form.
    :param treemap_path: A string combining the selected species and provoked/unprovoked status (e.g., 'White shark/Unprovoked').
    :param colorblind_active: Boolean indicating whether colorblind mode is enabled.
    :return: A Plotly Mapbox figure with markers sized by incident count; selected species are highlighted.
    """
    # Check for empty data
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

    # Add a 'Highlight' column to mark selected vs other points
    df_local["Highlight"] = "Other"
    if treemap_path:
        path_parts = treemap_path.split("/")
        species_sel = path_parts[0] if len(path_parts) >= 1 else None
        provoked_sel = path_parts[1] if len(path_parts) >= 2 else None

        mask = pd.Series([True]*len(df_local))
        if species_sel:
            mask &= (df_local["Shark.common.name"] == species_sel)
        if provoked_sel:
            mask &= (df_local["Provoked/unprovoked"] == provoked_sel)

        df_local.loc[mask, "Highlight"] = "Selected"

    # Aggregate by Latitude/Longitude and highlight
    bubble_data = (
        df_local.groupby(["Latitude", "Longitude", "Highlight"])
        .size()
        .reset_index(name="Count")
    )

    # Determine color palette for colorblind mode
    color_discrete_sequence = get_color_discrete_sequence(colorblind_active)

    # Create scatter map
    fig = px.scatter_mapbox(
        bubble_data,
        lat="Latitude",
        lon="Longitude",
        size="Count",
        hover_name="Count",
        color="Highlight",
        zoom=4,
        center={"lat": -25.0, "lon": 133.0},
        mapbox_style="open-street-map",
        color_discrete_sequence=color_discrete_sequence,
    )

    fig.update_traces(marker=dict(opacity=0.6), selector=dict(mode='markers'))
    fig.update_layout(
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
        dragmode="select"
    )
    return fig


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
    """
    Displaying the incident details in a modal
    when a map point is clicked by the user. It allows navigation (previous/next)
    in case of multiple incidents at the same coordinate.

    :param slider_range: Current indices [start_idx, end_idx] for the date slider.
    :param selectedSpecies: A list of species from the 'species-dropdown'.
    :param clickData: Data from clicking a point on the map.
    :param close_clicks: Number of times the modal 'Close' button has been clicked.
    :param prev_clicks: Number of times the 'Previous' button has been clicked in the modal.
    :param next_clicks: Number of times the 'Next' button has been clicked in the modal.
    :param store_data: Current state of the 'selected-incidents-store', including rows and current index.
    :return: A tuple to update the modal style, the stored incident data, the modal content, 
             previous/next button styles, and a className for background blur.
    """
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

    # Close if 'Close' button is clicked
    if "close-modal" in triggered_id:
        return default_style, default_store, default_content, prev_style, next_style, no_blur

    # Filter data by date range
    if slider_range:
        start_date = index_to_date[slider_range[0]]
        end_date = index_to_date[slider_range[1]]
        filter_df = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)]
    else:
        filter_df = df.copy()

    # Filter by selected species if any
    if selectedSpecies:
        filter_df = filter_df[filter_df["Shark.common.name"].isin(selectedSpecies)]

    # If the map was clicked, gather incident details for the clicked location's coordinates
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

    # Navigation: previous/next buttons
    if "prev-incident" in triggered_id:
        current_idx = max(0, current_idx - 1)
    elif "next-incident" in triggered_id:
        current_idx = min(len(rows) - 1, current_idx + 1)

    updated_store = {"rows": rows, "current_index": current_idx}
    content = build_modal_content(rows, current_idx)
    prev_style, next_style = get_nav_button_styles(len(rows), current_idx, prev_style, next_style)

    return modal_style, updated_store, content, prev_style, next_style, blurred


def build_modal_content(rows, idx):
    """
    Builds the content (text + image) displayed in the info modal,
    given a list of incident rows and the current index.

    :param rows: A list of dictionaries containing incident data.
    :param idx: The index of the currently displayed incident in 'rows'.
    :return: An HTML Div component containing text details and an image for the current incident.
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
    """
    Determines the display style of 'Previous' and 'Next' buttons
    based on the total rows and the current index.

    :param num_rows: Total number of incidents in the modal.
    :param current_idx: Current index of the displayed incident.
    :param prev_style: Base style dictionary for the 'Previous' button.
    :param next_style: Base style dictionary for the 'Next' button.
    :return: The updated style dictionaries for 'Previous' and 'Next' to show/hide them as needed.
    """
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


@app.callback(
    Output("third-chart", "figure"),
    [
        Input("filtered-data-store", "data"),
        Input("pie-selected-species", "data"),
        Input("histogram-type", "value"),
        Input("update-histogram-button", "n_clicks"),
        Input("colorblind-store", "data"),
    ],
)
def update_histogram(filtered_data, treemap_path, histogram_type, n_clicks, colorblind_active):
    """
    Updates the histogram based on the currently filtered data

    :param filtered_data: A list of dictionaries from the filtered dataset.
    :param treemap_path: A string with the selected species/provoked state from the stacked bar chart.
    :param histogram_type: One of 'age', 'state', 'month', 'dayofweek', 'sitecategory', or 'activity'.
    :param n_clicks: Number of times the 'Apply Selection' button has been clicked.
    :param colorblind_active: Boolean to toggle colorblind-friendly palettes.
    :return: A Plotly histogram (or bar chart) figure.
    """
    if not filtered_data:
        return px.scatter(title="No Data in Histogram")
    df_local = pd.DataFrame(filtered_data)
    if df_local.empty:
        return px.scatter(title="No Data in Histogram")

    # Apply species/provoked filter from the stacked bar
    if treemap_path:
        path_parts = treemap_path.split("/")
        species_sel = path_parts[0] if len(path_parts) >= 1 else None
        provoked_sel = path_parts[1] if len(path_parts) >= 2 else None

        mask = pd.Series([True] * len(df_local))
        if species_sel:
            mask &= (df_local["Shark.common.name"] == species_sel)
        if provoked_sel:
            mask &= (df_local["Provoked/unprovoked"] == provoked_sel)
        df_local = df_local[mask]

    # Choose which column to show on the x-axis
    if histogram_type == "age":
        df_local = df_local.dropna(subset=["Victim.age.group"])
        x_axis = "Victim.age.group"
        title = "Histogram: Victim Age Group"
    elif histogram_type == "dayofweek":
        df_local = df_local.dropna(subset=["DayOfWeek"])
        x_axis = "DayOfWeek"
        title = "Bar Chart: Day of Week"
    elif histogram_type == "state":
        df_local = df_local.dropna(subset=["State"])
        x_axis = "State"
        title = "Bar Chart: State"
    elif histogram_type == "month":
        df_local = df_local.dropna(subset=["Month"])
        x_axis = "Month"
        title = "Bar Chart: Month"
    elif histogram_type == "sitecategory":
        df_local = df_local.dropna(subset=["Site.category"])
        x_axis = "Site.category"
        title = "Bar Chart: Site Category"
    elif histogram_type == "activity":
        df_local = df_local.dropna(subset=["Victim.activity"])
        x_axis = "Victim.activity"
        title = "Bar Chart: Victim Activity"
    else:
        return px.scatter(title="Invalid Histogram Type")

    color_discrete_sequence = get_color_discrete_sequence(colorblind_active)

    # Build the histogram (or bar chart)
    fig = px.histogram(
        df_local,
        x=x_axis,
        category_orders={
            "Victim.age.group": custom_age_order, 
            "DayOfWeek": custom_day_order, 
            "Month": custom_month_order
        },
        title=title,
        barnorm=None,
        color_discrete_sequence=color_discrete_sequence,
    )

    fig.update_layout(
        clickmode="event+select",
        margin={"r": 0, "t": 40, "l": 0, "b": 0}
    )
    return fig


@app.callback(
    Output("pcp-graph", "figure"),
    [
        Input("filtered-data-store", "data"),
        Input("pie-selected-species", "data"),
        Input("colorblind-store", "data")
    ]
)
def update_pcp_graph_no_grouping(filtered_data, treemap_path, colorblind_active):
    """
    Updating the parallel coordinates plot to visualize numeric variables
    across incidents. The line color is determined by 'Victim.injury.num'.

    :param filtered_data: A list of dictionaries representing the filtered dataset.
    :param treemap_path: Optional string from the stacked bar to filter by species/provoked.
    :param colorblind_active: Boolean to toggle a colorblind-friendly color scale.
    :return: A Plotly 'Parcoords' figure encoding numeric dimensions and injury severity.
    """
    if not filtered_data:
        return px.scatter(title="No Data in PCP")

    df_local = pd.DataFrame(filtered_data)
    if df_local.empty:
        return px.scatter(title="No Data in PCP")

    # Apply filter from stacked bar (species/provoked)
    if treemap_path:
        path_parts = treemap_path.split("/")
        species_sel = path_parts[0] if len(path_parts) >= 1 else None
        provoked_sel = path_parts[1] if len(path_parts) >= 3 else None

        mask = pd.Series([True]*len(df_local))
        if species_sel:
            mask &= (df_local["Shark.common.name"] == species_sel)
        if provoked_sel:
            mask &= (df_local["Provoked/unprovoked"] == provoked_sel)
        df_local = df_local[mask]

    # Numeric columns for the PCP
    numeric_cols = [
        "Distance.to.shore.m",
        "Depth.of.incident.m",
        "Total.water.depth.m",
        "Time.in.water.min"
    ]
    for c in numeric_cols:
        df_local[c] = pd.to_numeric(df_local[c], errors="coerce")

    # Drop rows where any needed column is NaN
    df_local = df_local.dropna(subset=numeric_cols)
    if df_local.empty:
        return px.scatter(title="No Data for PCP")

    # Choose color scale based on colorblind mode
    color_map = px.colors.sequential.Cividis if colorblind_active else px.colors.sequential.Bluered

    # Create Parallel Coordinates Plot using plotly.graph_objects
    fig = go.Figure(data=go.Parcoords(
        line=dict(
            color=df_local['Victim.injury.num'],
            colorscale=color_map,
            showscale=True,
            cmin=df_local['Victim.injury.num'].min(),
            cmax=df_local['Victim.injury.num'].max(),
        ),
        dimensions=[
            dict(
                label="Shore Dist (m)",
                values=df_local["Distance.to.shore.m"],
                range=[df_local["Distance.to.shore.m"].min(), 4000],
                constraintrange=[10, 50]  # Example highlighted range
            ),
            dict(
                label="Incident Depth (m)",
                values=df_local["Depth.of.incident.m"],
                range=[df_local["Depth.of.incident.m"].min(), df_local["Depth.of.incident.m"].max()],
            ),
            dict(
                label="Total Water Depth (m)",
                values=df_local["Total.water.depth.m"],
                range=[df_local["Total.water.depth.m"].min(), df_local["Total.water.depth.m"].max()],
            ),
            dict(
                label="Time in Water (min)",
                values=df_local["Time.in.water.min"],
                range=[df_local["Time.in.water.min"].min(), df_local["Time.in.water.min"].max()],
            )
        ]
    ))

    fig.update_layout(title="Parallel Coordinates Plot")
    return fig


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
    """
    Opens help modal. Clicking 'Help' shows it;
    clicking 'Close' hides it.

    :param help_clicks: The number of times the 'Help' button has been clicked.
    :param close_help_clicks: The number of times the 'Close' button on the modal has been clicked.
    :return: A tuple controlling the modal's style and the background blur className.
    """
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

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
    if triggered_id == "close-help-modal":
        return {"display": "none"}, ""
    raise PreventUpdate


@app.callback(
    Output("temp-bin-selection", "data", allow_duplicate=True),
    Input("third-chart", "clickData"),
    [
        State("temp-bin-selection", "data"),
        State("histogram-type", "value"),
    ],
    prevent_initial_call=True
)
def accumulate_temp_bins(click_data, temp_store, current_hist_type):
    """
    Temporarily collects bin selections on the histogram.
    The selections only apply when 'Apply Selection' is clicked.

    :param click_data: Data about the histogram bin that was clicked.
    :param temp_store: The existing temporary bin selections dictionary.
    :param current_hist_type: The currently chosen histogram dimension (e.g. 'age', 'state').
    :return: An updated dictionary reflecting toggled bin selections.
    """
    if not click_data or "points" not in click_data or not click_data["points"]:
        raise PreventUpdate

    bin_clicked = click_data["points"][0].get("x")
    if temp_store is None:
        temp_store = {"hist_type": current_hist_type, "values": []}

    # If histogram type changed, reset the selections
    if temp_store["hist_type"] != current_hist_type:
        temp_store = {"hist_type": current_hist_type, "values": []}

    # Toggle the clicked bin
    if bin_clicked in temp_store["values"]:
        temp_store["values"].remove(bin_clicked)
    else:
        temp_store["values"].append(bin_clicked)

    return temp_store


@app.callback(
    [
        Output("selected-bins", "data", allow_duplicate=True),
        Output("temp-bin-selection", "data"),
    ],
    Input("clear-histogram-selection", "n_clicks"),
    prevent_initial_call=True
)
def clear_bin_selections(n_clicks):
    """
    Clears both the main 'selected-bins' store and the temporary bin selection.
    
    :param n_clicks: Number of times the 'Clear Selection' button has been clicked.
    :return: A tuple with two empty selection dictionaries.
    """
    if n_clicks is None:
        raise PreventUpdate

    empty_selection = {"hist_type": None, "values": []}
    return empty_selection, empty_selection


@app.callback(
    Output("selected-bins", "data", allow_duplicate=True),
    Input("update-histogram-button", "n_clicks"),
    State("temp-bin-selection", "data"),
    prevent_initial_call=True
)
def apply_selected_bins(n_clicks, temp_selection):
    """
    Moves the temporarily stored bin selections ('temp-bin-selection')
    into the main 'selected-bins' store, effectively applying the filter.

    :param n_clicks: Number of times the 'Apply Selection' button has been clicked.
    :param temp_selection: The temporary bin selections dictionary to be applied.
    :return: The updated selections to store in 'selected-bins'.
    """
    if n_clicks is None or not temp_selection:
        raise PreventUpdate

    return temp_selection


# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)

