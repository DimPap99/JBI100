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

# Load and preprocess shark incident data
df = pd.read_csv("shark.csv")  # Replace with the path to your dataset
df = df.dropna(subset=["Latitude", "Longitude"])  # Ensure valid Latitude and Longitude
df["Date"] = pd.to_datetime(df["Incident.year"].astype(str) + "-" + df["Incident.month"].astype(str), errors="coerce")

# Compute additional attributes for analysis
df["Fatal"] = df["Injury.severity"].str.contains("fatal", case=False, na=False)
df["Non-Fatal"] = ~df["Fatal"]

# Dropdown options for shark species
species_options = [
    {"label": species, "value": species}
    for species in df["Shark.common.name"].dropna().unique()
]

# Layout of the app
app.layout = html.Div(
    children=[
        html.Div(
            className="row",
            children=[
                html.Div(
                    className="four columns div-user-controls",
                    children=[
                        html.H2("DASH - SHARK INCIDENT DATA"),
                        html.P("Select different days using the date picker."),
                        dcc.DatePickerSingle(
                            id="date-picker",
                            min_date_allowed=dt(1791, 1, 1),
                            max_date_allowed=dt(2022, 12, 31),
                            initial_visible_month=dt(2022, 1, 1),
                            date=dt(2022, 1, 1).date(),
                            display_format="MMMM D, YYYY",
                        ),
                        dcc.Dropdown(
                            id="species-dropdown",
                            options=species_options,
                            placeholder="Select a Shark Species",
                        ),
                        html.H3("Analyze Shark Species"),
                        dcc.Graph(id="diverging-bar-chart"),
                    ],
                ),
                html.Div(
                    className="eight columns div-for-charts bg-grey",
                    children=[
                        dcc.Graph(id="map-graph", config={"scrollZoom": True}),
                    ],
                ),
            ],
        ),
    ]
)

@app.callback(
    Output("map-graph", "figure"),
    [Input("date-picker", "date"), Input("species-dropdown", "value"), Input("map-graph", "clickData")],
)
def update_graph(datePicked, selectedSpecies, clickData):
    date_picked = pd.to_datetime(datePicked)
    filtered_df = df[(df["Date"].dt.month == date_picked.month) & (df["Date"].dt.day == date_picked.day)]

    if selectedSpecies:
        filtered_df = filtered_df[filtered_df["Shark.common.name"] == selectedSpecies]

    bubble_data = filtered_df.groupby(["Latitude", "Longitude"]).size().reset_index(name="Incident Count")
    zoom_level = 4
    center = {"lat": -25.0, "lon": 133.0}

    if clickData:
        clicked_point = clickData["points"][0]
        center = {"lat": float(clicked_point["lat"]), "lon": float(clicked_point["lon"])}
        zoom_level = 8

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
    Output("diverging-bar-chart", "figure"),
    [Input("species-dropdown", "value")],
)
def update_diverging_bar_chart(selectedSpecies):
    if not selectedSpecies:
        return px.bar(title="Select a Shark Species for Analysis")

    # Aggregate data for analysis
    grouped_data = df.groupby("Shark.common.name").agg(
        Incidents=("Shark.common.name", "count"),
        Fatalities=("Fatal", "sum"),
        NonFatal=("Non-Fatal", "sum"),
    ).reset_index()

    # Reshape data for diverging bar chart
    melted_data = grouped_data.melt(
        id_vars="Shark.common.name",
        value_vars=["Incidents", "Fatalities", "NonFatal"],
        var_name="Category",
        value_name="Count",
    )

    # Filter for the selected species
    filtered_data = melted_data[melted_data["Shark.common.name"] == selectedSpecies]

    # Diverging bar chart
    fig = px.bar(
        filtered_data,
        x="Count",
        y="Category",
        color="Category",
        orientation="h",
        title=f"Analysis of {selectedSpecies}",
        color_discrete_sequence=px.colors.qualitative.Set2,  # Categorical colormap
    )
    fig.update_layout(
        xaxis_title="Number of Incidents",
        yaxis_title="Category",
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
    )
    return fig

if __name__ == "__main__":
    app.run_server(debug=True)