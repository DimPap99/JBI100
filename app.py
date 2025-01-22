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

def categorical_to_numerical(field_name, data):
    custom_mapping = {}
    unique_categories = data[field_name].unique()
    for idx, category in enumerate(unique_categories):
        custom_mapping[category] = idx + 1
    mapped_column = field_name + '.mapped'
    mapped_column = str(mapped_column)
    data[mapped_column] = data[field_name].map(custom_mapping)
    return data

## Site.category cleaning
df["Site.category"] = df["Site.category"].replace(
    ['Coastal','Ocean/pelagic', 'other: fish farm'],
    ['coastal','ocean/pelagic', 'fish farm']
)
df = categorical_to_numerical('Site.category', df)

## Injury.severity
df["Injury.severity"] = df["Injury.severity"].replace(
    ['other: teeth marks', 'fatality'],
    ['teeth marks','fatal']
)

## Final PCP data
df["Distance.to.shore.m"] = pd.to_numeric(df.get("Distance.to.shore.m"), errors="coerce")
df["Total.water.depth.m"] = pd.to_numeric(df.get("Total.water.depth.m"), errors="coerce")
df["Time.in.water.min"] = pd.to_numeric(df.get("Time.in.water.min"), errors="coerce")
df["Depth.of.incident.m"] = pd.to_numeric(df.get("Depth.of.incident.m"), errors="coerce")

df["Victim.age"] = pd.to_numeric(df.get("Victim.age"), errors="coerce")

custom_month_order = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]
custom_day_order = [
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
]

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
# App Layout
# ------------------------------------------------------------------------------
app.layout = html.Div([
    html.Div(
        id="background-container",
        children=[
            html.Div(
                className="row",
                children=[
                    # Left Column (Controls) + Third Chart
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
                                html.Button("Help",
                                    id="help-button",
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
                                        value="age",
                                        inline=True,
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
                                            # Put the title + button in a small row container:
                                            html.Div(
                                                style={"display": "flex", "alignItems": "center"},
                                                children=[
                                                    html.H4("Parallel Coordinates Plot", style={"paddingLeft": "12px", "marginRight": "10px"}),
                                                    # html.Button(
                                                    #     "Show Mapping",
                                                    #     id="show-mapping-button",
                                                    #     n_clicks=0,
                                                    #     style={"padding": "5px 10px"}
                                                    # ),
                                                ],
                                            ),

                                            # The PCP graph as before
                                            dcc.Graph(
                                                id="pcp-graph",
                                                style={"height": "85%", "width": "100%"}
                                            ),
                                            
                                            ## Mapping infomation
                                            # html.Div(
                                            #     id="mapping-info",
                                            #     style={
                                            #         "display": "none",
                                            #         "position": "fixed",
                                            #         "top": "20%",
                                            #         "left": "30%",
                                            #         "width": "40%",
                                            #         "height": "auto",
                                            #         "backgroundColor": "white",
                                            #         "boxShadow": "0px 0px 10px rgba(0, 0, 0, 0.5)",
                                            #         "zIndex": 1000,
                                            #         "padding": "20px",
                                            #         "borderRadius": "10px"},
                                            #         children=[
                                            #             html.Button("Close", id="close-modal", style={"float": "right", "margin": "10px"}),
                                            #             html.Div(
                                            #             children=[
                                            #             ],
                                            #             style={"color": "black"},
                                            #         ),
                                            #     ],
                                            # ),
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
    dcc.Store(id="filtered-data-store"),
    dcc.Store(id="pie-selected-species", data=None),
    dcc.Store(id="histogram-click-store", data=None),

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
                        "This dashboard provides an interactive interface for exploring "
                        "shark incident data in Australia. Use the filters on the left to "
                        "narrow down the data by date range, species, location, and more. "
                        "Click on elements in the charts to focus on specific subsets of the data."
                    ),
                    html.P(
                        "For example, click on a bar in the histogram to filter incidents by victim age. "
                        "Use the map to explore incidents geographically and see details by clicking on a point."
                    ),
                ],
                style={"color": "black"},
            ),
        ],
    ),
])


# ------------------------------------------------------------------------------
# 1) Single Callback to Handle "Apply" AND "Reset"
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
        default_species = []
        default_map_selection = None
        default_month = []
        default_dow = []
        default_victim_activity = []
        default_state = []
        default_hist_age = None

        return (
            default_start,
            default_end,
            default_slider_range,
            default_species,
            default_map_selection,
            default_month,
            default_dow,
            default_victim_activity,
            default_state,
            default_hist_age
        )

    raise PreventUpdate


# ------------------------------------------------------------------------------
# 2) COMBINED callback for treemap-click + reset => set pie-selected-species
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
@app.callback(
    Output("histogram-click-store", "data"),
    [
        Input("third-chart", "clickData"),
        Input("reset-button", "n_clicks")
    ],
    [State("histogram-type", "value")],
    prevent_initial_call=True
)
def handle_histogram_click(click_data, reset_clicks, histogram_type):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate

    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if triggered_id == "third-chart" and click_data:
        clicked_value = click_data["points"][0].get("x")
        return {"type": histogram_type, "value": clicked_value}

    elif triggered_id == "reset-button":
        return None

    raise PreventUpdate


# ------------------------------------------------------------------------------
# 3) “Master” Filtering Callback
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
        Input("histogram-click-store", "data"),
    ]
)
def update_filtered_data_store(
    slider_range, selected_states, selected_species,
    map_selected, selected_months, selected_dows,
    selected_activities, histogram_click_data
):
    filtered_df_local = df.copy()

    if slider_range:
        start_date = index_to_date[slider_range[0]]
        end_date = index_to_date[slider_range[1]]
        filtered_df_local = filtered_df_local[
            (filtered_df_local["Date"] >= start_date) &
            (filtered_df_local["Date"] <= end_date)
        ]

    if histogram_click_data and histogram_click_data["type"] == "state":
        filtered_df_local = filtered_df_local[
            filtered_df_local["State"] == histogram_click_data["value"]
        ]
    elif selected_states:
        filtered_df_local = filtered_df_local[
            filtered_df_local["State"].isin(selected_states)
        ]

    if selected_species:
        filtered_df_local = filtered_df_local[
            filtered_df_local["Shark.common.name"].isin(selected_species)
        ]

    if histogram_click_data and histogram_click_data["type"] == "month":
        filtered_df_local = filtered_df_local[
            filtered_df_local["Month"] == histogram_click_data["value"]
        ]
    elif selected_months:
        filtered_df_local = filtered_df_local[
            filtered_df_local["Month"].isin(selected_months)
        ]

    if histogram_click_data and histogram_click_data["type"] == "dayofweek":
        filtered_df_local = filtered_df_local[
            filtered_df_local["DayOfWeek"] == histogram_click_data["value"]
        ]
    elif selected_dows:
        filtered_df_local = filtered_df_local[
            filtered_df_local["DayOfWeek"].isin(selected_dows)
        ]

    if selected_activities:
        filtered_df_local = filtered_df_local[
            filtered_df_local["Victim.activity"].isin(selected_activities)
        ]

    if histogram_click_data and histogram_click_data["type"] == "age":
        filtered_df_local = filtered_df_local[
            filtered_df_local["Victim.age"] == histogram_click_data["value"]
        ]

    return filtered_df_local.to_dict("records")


# ------------------------------------------------------------------------------
# 4) Build Treemap (here replaced by Stacked Bar) from filtered data
# ------------------------------------------------------------------------------
@app.callback(
    Output("pie-chart", "figure"),
    Input("filtered-data-store", "data")
)
def update_treemap_from_filtered_data(filtered_data):
    if not filtered_data:
        empty_df = pd.DataFrame({
            "Shark.common.name": [],
            "Site.category": [],
            "Count": []
        })
        fig = px.bar(
            empty_df,
            x="Shark.common.name",
            y="Count",
            title="No Data",
            template="none",
        )
        fig.update_layout(clickmode='event+select')
        return fig

    filtered_df_local = pd.DataFrame(filtered_data)
    if filtered_df_local.empty:
        empty_df = pd.DataFrame({
            "Shark.common.name": [],
            "Site.category": [],
            "Count": []
        })
        fig = px.bar(
            empty_df,
            x="Shark.common.name",
            y="Count",
            title="No Data",
            template="none",
        )
        fig.update_layout(clickmode='event+select')
        return fig
    
    bar_data = (
        filtered_df_local
        .groupby(["Shark.common.name", "Site.category"])
        .size()
        .reset_index(name="Count")
    )

    bar_data["StackLabel"] = (
        bar_data["Site.category"]
    )

    fig = px.bar(
        bar_data,
        x="Shark.common.name",
        y="Count",
        color="StackLabel",
        barmode="stack",
        title="Shark Incidents (Stacked Bar Chart: Species vs. Site)",
        template="none"  
    )
    fig.update_layout(clickmode='event+select')
    return fig

# ------------------------------------------------------------------------------
# 5) Update Map
# ------------------------------------------------------------------------------
@app.callback(
    Output("map-graph", "figure"),
    [
        Input("filtered-data-store", "data"),
        Input("pie-selected-species", "data")
    ]
)
def update_map_from_filtered_data_and_treemap_path(filtered_data, treemap_path):
    if not filtered_data:
        return px.scatter_mapbox(
            pd.DataFrame({"Latitude": [], "Longitude": [], "Incident Count": []}),
            lat="Latitude", lon="Longitude", size="Incident Count",
            zoom=4, center={"lat": -25.0, "lon": 133.0},
            mapbox_style="open-street-map",
            title="No Data"
        )

    df_local = pd.DataFrame(filtered_data)
    if df_local.empty:
        return px.scatter_mapbox(
            pd.DataFrame({"Latitude": [], "Longitude": [], "Incident Count": []}),
            lat="Latitude", lon="Longitude", size="Incident Count",
            zoom=4, center={"lat": -25.0, "lon": 133.0},
            mapbox_style="open-street-map",
            title="No Data"
        )

    df_local["Highlight"] = "Other"
    if treemap_path:
        # For stacked bar path: "Species / Site / Provoked"
        path_parts = treemap_path.split("/")
        species_sel = path_parts[0] if len(path_parts) >= 1 else None
        # site_sel = path_parts[1] if len(path_parts) >= 2 else None
        # provoked_sel = path_parts[2] if len(path_parts) >= 3 else None

        mask = pd.Series([True]*len(df_local))
        if species_sel:
            mask &= (df_local["Shark.common.name"] == species_sel)
        df_local.loc[mask, "Highlight"] = "Selected"

    bubble_data = (
        df_local.groupby(["Latitude", "Longitude", "Highlight"])
        .size()
        .reset_index(name="Count")
    )

    fig = px.scatter_mapbox(
        bubble_data,
        lat="Latitude",
        lon="Longitude",
        size="Count",
        hover_name="Count",
        color="Highlight",
        zoom=4,
        center={"lat": -25.0, "lon": 133.0},
        mapbox_style="open-street-map"
    )
    fig.update_traces(marker=dict(opacity=0.6), selector=dict(mode='markers'))
    fig.update_layout(
        coloraxis=dict(
            colorscale=[
                [0, "blue"],
                [0.5, "blue"],
                [0.5, "red"],
                [1, "red"],
            ],
            showscale=False,
        ),
        title="Shark Incidents Density",
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
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
# 7) Third Chart: Histogram
# ------------------------------------------------------------------------------
@app.callback(
    Output("third-chart", "figure"),
    [
        Input("filtered-data-store", "data"),
        Input("pie-selected-species", "data"),
        Input("histogram-type", "value"),
    ]
)
def update_histogram(filtered_data, treemap_path, histogram_type):
    if not filtered_data:
        return px.scatter(title="No Data in Histogram")

    df_local = pd.DataFrame(filtered_data)
    if df_local.empty:
        return px.scatter(title="No Data in Histogram")

    if treemap_path:
        path_parts = treemap_path.split("/")
        species_sel = path_parts[0] if len(path_parts) >= 1 else None
        mask = pd.Series([True] * len(df_local))
        if species_sel:
            mask &= (df_local["Shark.common.name"] == species_sel)
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
    fig.update_layout(
        clickmode="event+select",
        margin={"r": 0, "t": 40, "l": 0, "b": 0}
    )
    return fig


# ------------------------------------------------------------------------------
# 8) PCP
# ------------------------------------------------------------------------------
@app.callback(
    Output("pcp-graph", "figure"),
    [
        Input("filtered-data-store", "data"),
        Input("pie-selected-species", "data")
    ]
)
def update_pcp_graph_no_grouping(filtered_data, treemap_path):
    if not filtered_data:
        return px.scatter(title="No Data in PCP")

    df_local = pd.DataFrame(filtered_data)
    if df_local.empty:
        return px.scatter(title="No Data in PCP")

    # Again, same subfilter logic for stacked bar 'path'
    if treemap_path:
        path_parts = treemap_path.split("/")
        species_sel = path_parts[0] if len(path_parts) >= 1 else None
        mask = pd.Series([True]*len(df_local))
        if species_sel:
            mask &= (df_local["Shark.common.name"] == species_sel)
        df_local = df_local[mask]

    numeric_cols = [
        "Distance.to.shore.m",
        "Depth.of.incident.m",
        "Total.water.depth.m",
        "Time.in.water.min"       
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
            "Distance.to.shore.m": "Distance (m) ",
            "Total.water.depth.m": "Total Depth (m)",
            "Depth.of.incident.m": "Depth of Incident (m)",
            "Time.in.water.min": "Time (min)"     
        }
    )
    fig.update_traces(line_color="blue")
    fig.update_layout(title="")
    return fig


# ------------------------------------------------------------------------------
# Show numeric-to-categorical mapping for Site/Injury
# ------------------------------------------------------------------------------
# @app.callback(
#     Output("mapping-info", "children"),
#     [
#         Input("filtered-data-store", "data"),
#         Input("pie-selected-species", "data")
#         #Input("mapping-info", "n_clicks"),
#     ]
# )
# def display_mapped_legend(filtered_data, treemap_path, show_clicks):
#     """
#     Prints a mini legend showing how numeric columns
#     'Site.category.mapped' and 'Injury.severity.mapped'
#     correspond to their original text values,
#     but only after the user clicks the "Show Mapping" button.
#     """
#     if show_clicks == 0:
#         return ""  # or "Click 'Show Mapping' to see numeric→category translations."

#     if not filtered_data:
#         return "No data available for mapping legend."

#     df_local = pd.DataFrame(filtered_data)
#     if df_local.empty:
#         return "No data available for mapping legend."

#     # Match subfilter logic from PCP:
#     if treemap_path:
#         path_parts = treemap_path.split("/")
#         species_sel = path_parts[0] if len(path_parts) >= 1 else None

#         mask = pd.Series([True]*len(df_local))
#         if species_sel:
#             mask &= (df_local["Shark.common.name"] == species_sel)
#         df_local = df_local[mask]

#     # Gather unique numeric->text pairs for site
#     site_pairs = (
#         df_local[["Site.category.mapped", "Site.category"]]
#         .dropna().drop_duplicates()
#         .sort_values("Site.category.mapped")
#     )
#     site_lines = [
#         f"{int(row['Site.category.mapped'])} => {row['Site.category']}"
#         for _, row in site_pairs.iterrows()
#     ]

#     # Gather unique numeric->text pairs for injury
#     inj_pairs = (
#         df_local[["Injury.severity.mapped", "Injury.severity"]]
#         .dropna().drop_duplicates()
#         .sort_values("Injury.severity.mapped")
#     )
#     inj_lines = [
#         f"{int(row['Injury.severity.mapped'])} => {row['Injury.severity']}"
#         for _, row in inj_pairs.iterrows()
#     ]

#     if not site_lines and not inj_lines:
#         return "No mapped categories in this subset."

#     text_output = []
#     if site_lines:
#         text_output.append("Site.category.mapped:\n" + "\n".join(site_lines) + "\n")
#     if inj_lines:
#         text_output.append("Injury.severity.mapped:\n" + "\n".join(inj_lines) + "\n")

#     return "\n".join(text_output)


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


# ------------------------------------------------------------------------------
# Run
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    app.run_server(debug=True)
