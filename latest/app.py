import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
from dash.dependencies import State, Input, Output
from dash.exceptions import PreventUpdate

import pandas as pd
import os
import networkx as nx

app = dash.Dash(
    __name__,
    meta_tags=[
        {
            "name": "viewport",
            "content": "width=device-width, initial-scale=1, maximum-scale=1.0, user-scalable=no",
        }
    ],
)
server = app.server

app.config["suppress_callback_exceptions"] = True

# Plotly mapbox token
mapbox_access_token = "pk.eyJ1IjoicGxvdGx5bWFwYm94IiwiYSI6ImNrOWJqb2F4djBnMjEzbG50amg0dnJieG4ifQ.Zme1-Uzoi75IaFbieBDl3A"

state_map = {
    "numpy": "numpy",
    "plotly": "plotly"
}

state_list = ['numpy', 'plotly'] # list(state_map.keys())

# Load data
data_dict = {}
for state in state_list:
    p = os.getcwd().split(os.path.sep)
    csv_path = "data/processed/df_{}_lat_lon.csv".format(state)
    state_data = pd.read_csv(csv_path)
    data_dict[state] = state_data

# Cost Metric
cost_metric = [
    "Average Covered Charges",
    "Average Total Payments",
    "Average Medicare Payments",
]

# init_region = data_dict[state_list[0]][
#     "Hospital Referral Region (HRR) Description"
# ].unique()

init_region = ['numpy', 'plotly']

def generate_aggregation(df, metric):
    aggregation = {
        metric[0]: ["min", "mean", "max"],
        metric[1]: ["min", "mean", "max"],
        metric[2]: ["min", "mean", "max"],
    }
    grouped = (
        df.groupby(["Hospital Referral Region (HRR) Description", "Provider Name"])
        .agg(aggregation)
        .reset_index()
    )

    grouped["lat"] = grouped["lon"] = grouped["Provider Street Address"] = grouped[
        "Provider Name"
    ]
    grouped["lat"] = grouped["lat"].apply(lambda x: get_lat_lon_add(df, x)[0])
    grouped["lon"] = grouped["lon"].apply(lambda x: get_lat_lon_add(df, x)[1])
    grouped["Provider Street Address"] = grouped["Provider Street Address"].apply(
        lambda x: get_lat_lon_add(df, x)[2]
    )

    return grouped


def get_lat_lon_add(df, name):
    return [
        df.groupby(["Provider Name"]).get_group(name)["lat"].tolist()[0],
        df.groupby(["Provider Name"]).get_group(name)["lon"].tolist()[0],
        df.groupby(["Provider Name"])
        .get_group(name)["Provider Street Address"]
        .tolist()[0],
    ]


def build_upper_left_panel():
    return html.Div(
        id="upper-left",
        className="six columns",
        children=[
            html.P(
                className="section-title",
                children="Choose library on the plot or from the list below to see dependency details",
            ),
            html.Div(
                className="control-row-1",
                children=[
                    html.Div(
                        id="state-select-outer",
                        children=[
                            html.Label("Select a State"),
                            dcc.Dropdown(
                                id="state-select",
                                options=[{"label": i, "value": i} for i in state_list],
                                value=state_list[0],
                            ),
                        ],
                    ),
                    html.Div(
                        id="select-metric-outer",
                        children=[
                            html.Label("Choose a Cost Metric"),
                            dcc.Dropdown(
                                id="metric-select",
                                options=[{"label": i, "value": i} for i in cost_metric],
                                value=cost_metric[0],
                            ),
                        ],
                    ),
                ],
                style={'display': 'None'},
            ),
            html.Div(
                id="region-select-outer",
                className="control-row-2",
                children=[
                    html.Label("Select libraries"),
                    html.Div(
                        id="library-checklist-container",
                        children=dcc.Checklist(
                            id="region-select-all",
                            options=[{"label": "Select All Libraries", "value": "All"}],
                            value=[],
                            style={'display': 'None'}
                        ),
                    ),
                    html.Div(
                        id="region-select-dropdown-outer",
                        children=dcc.Dropdown(
                            id="region-select", multi=True, searchable=True,
                        ),
                    ),
                    html.Label("Select measures"),
                    html.Div(
                        id="measure-checklist-container",
                        children=dcc.Checklist(
                            id="measure-select-all",
                            options=[{"label": "Select All Measures", "value": "All"}],
                            value=[],
                        ),
                    ),
                    html.Div(
                        id="measure-select-dropdown-outer",
                        children=dcc.Dropdown(
                            id="measure-select", multi=True, searchable=True,
                        ),
                    ),
                ],
            ),
            html.Div(
                id="table-container",
                className="table-container",
                children=[
                    html.Div(
                        id="table-upper",
                        children=[
                            html.P("Library details"),
                            dcc.Loading(children=html.Div(id="cost-stats-container")),
                        ],
                    ),
                    html.Div(
                        id="table-lower",
                        children=[
                            html.P("Selected library dependency details"),
                            dcc.Loading(
                                children=html.Div(id="procedure-stats-container")
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )

# Source: https://plotly.com/python/network-graphs/
def generate_geo_map(geo_data, selected_metric, region_select, procedure_select):
    # Placeholder filtering code
    filtered_data = geo_data[
        geo_data["Hospital Referral Region (HRR) Description"].isin(region_select)
    ]

    colors = ["#21c7ef", "#76f2ff", "#ff6969", "#ff1717"]

    hospitals = []

    lat = filtered_data["lat"].tolist()
    lon = filtered_data["lon"].tolist()
    average_covered_charges_mean = filtered_data[selected_metric]["mean"].tolist()
    regions = filtered_data["Hospital Referral Region (HRR) Description"].tolist()
    provider_name = filtered_data["Provider Name"].tolist()

    data = go.Parcoords(
        line_color='blue',
        dimensions = list([
            dict(range = [1,5],
                constraintrange = [1,2], # change this range by dragging the pink line
                label = 'Rank', values = [1,4]),
            dict(range = [1.5,5],
                tickvals = [1.5,3,4.5],
                label = 'Stars', values = [3,1.5]),
            dict(range = [1,5],
                tickvals = [1,2,4,5],
                label = 'Dependent Repos', values = [2,4],
                ticktext = ['text 1', 'text 2', 'text 3', 'text 4']),
            dict(range = [1,5],
                label = 'Dependants', values = [4,2])
        ])
    )

    layout = go.Layout(
        showlegend=False,
        hovermode="closest",
        dragmode="select",
        clickmode="event+select",
        xaxis=dict(
            zeroline=False,
            automargin=True,
            showticklabels=True,
            title=dict(text="Procedure Cost", font=dict(color="#737a8d")),
            linecolor="#737a8d",
            tickfont=dict(color="#737a8d"),
            type="log",
        ),
        yaxis=dict(
            automargin=True,
            showticklabels=True,
            tickfont=dict(color="#737a8d"),
            gridcolor="#171b26",
        ),
        plot_bgcolor="#171b26",
        paper_bgcolor="#171b26",
    )

    return {"data": [data], "layout": layout}


def generate_procedure_plot(raw_data, cost_select, region_select, provider_select):
    procedure_data = raw_data[
        raw_data["Hospital Referral Region (HRR) Description"].isin(region_select)
    ].reset_index()

    traces = []
    selected_index = procedure_data[
        procedure_data["Provider Name"].isin(provider_select)
    ].index

    text = (
        procedure_data["Provider Name"]
        + "<br>"
        + "<b>"
        + procedure_data["DRG Definition"].map(str)
        + "/<b> <br>"
        + "Average Procedure Cost: $ "
        + procedure_data[cost_select].map(str)
    )

    # hoverinfo="text",
    # hovertext=text,
    # selectedpoints=selected_index,
    # hoveron="points",

        # Create random graph
    G = nx.random_geometric_graph(200, 0.125)

    # Create Edges
    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = G.nodes[edge[0]]['pos']
        x1, y1 = G.nodes[edge[1]]['pos']
        edge_x.append(x0)
        edge_x.append(x1)
        edge_x.append(None)
        edge_y.append(y0)
        edge_y.append(y1)
        edge_y.append(None)

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.5, color='#888'),
        hoverinfo='none',
        mode='lines')

    node_x = []
    node_y = []
    for node in G.nodes():
        x, y = G.nodes[node]['pos']
        node_x.append(x)
        node_y.append(y)

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers',
        hoverinfo='text',
        marker=dict(
            showscale=True,
            # colorscale options
            #'Greys' | 'YlGnBu' | 'Greens' | 'YlOrRd' | 'Bluered' | 'RdBu' |
            #'Reds' | 'Blues' | 'Picnic' | 'Rainbow' | 'Portland' | 'Jet' |
            #'Hot' | 'Blackbody' | 'Earth' | 'Electric' | 'Viridis' |
            colorscale='YlGnBu',
            reversescale=True,
            color=[],
            size=10,
            colorbar=dict(
                thickness=15,
                title='Node Connections',
                xanchor='left',
                titleside='right'
            ),
            line_width=2))

    # Color node points
    node_adjacencies = []
    node_text = []
    for node, adjacencies in enumerate(G.adjacency()):
        node_adjacencies.append(len(adjacencies[1]))
        node_text.append('# of connections: '+str(len(adjacencies[1])))

    node_trace.marker.color = node_adjacencies
    node_trace.text = node_text

    # Create Network Graph
    data = [edge_trace, node_trace]

    layout = layout=go.Layout(
            # title='<br>Network graph made with Python',
            # titlefont_size=16,
            # margin=dict(b=20,l=5,r=5,t=40),
            margin=dict(l=10, r=10, t=20, b=10, pad=5),
            plot_bgcolor="#171b26",
            paper_bgcolor="#171b26",
            clickmode="event+select",
            hovermode="closest",
            showlegend=False,
            # annotations=[ dict(
            #     text="Python code: <a href='https://plotly.com/ipython-notebooks/network-graphs/'> https://plotly.com/ipython-notebooks/network-graphs/</a>",
            #     showarrow=False,
            #     xref="paper", yref="paper",
            #     x=0.005, y=-0.002 ) ],
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
    
    # x : procedure, y: cost,
    return {"data": data, "layout": layout}


app.layout = html.Div(
    className="container scalable",
    children=[
        html.Div(
            id="banner",
            className="banner",
            children=[
                html.H6("Library Evaluation Dashboard"),
                html.Img(src=app.get_asset_url("plotly_logo_white.png")),
            ],
        ),
        html.Div(
            id="upper-container",
            className="row",
            children=[
                build_upper_left_panel(),
                html.Div(
                    id="geo-map-outer",
                    className="six columns",
                    children=[
                        html.P(
                            id="map-title",
                            children="Medicare Provider Charges in the State of {}".format(
                                state_map[state_list[0]]
                            ),
                        ),
                        html.Div(
                            id="geo-map-loading-outer",
                            children=[
                                dcc.Loading(
                                    id="loading",
                                    children=dcc.Graph(
                                        id="geo-map",
                                        figure={
                                            "data": [],
                                            "layout": dict(
                                                plot_bgcolor="#171b26",
                                                paper_bgcolor="#171b26",
                                            ),
                                        },
                                    ),
                                )
                            ],
                        ),
                    ],
                ),
            ],
        ),
        html.Div(
            id="lower-container",
            children=[
                dcc.Graph(
                    id="procedure-plot",
                    figure=generate_procedure_plot(
                        data_dict[state_list[0]], cost_metric[0], init_region, []
                    ),
                )
            ],
        ),
    ],
)


@app.callback(
    [
        Output("region-select", "value"),
        Output("region-select", "options"),
        Output("map-title", "children"),
    ],
    [Input("region-select-all", "value"), Input("state-select", "value"),],
)
def update_region_dropdown(select_all, state_select):
    state_raw_data = data_dict[state_select]
    regions = ['numpy', 'plotly'] # state_raw_data["Hospital Referral Region (HRR) Description"].unique()
    options = [{"label": i, "value": i} for i in regions]

    ctx = dash.callback_context
    if ctx.triggered[0]["prop_id"].split(".")[0] == "region-select-all":
        if select_all == ["All"]:
            value = [i["value"] for i in options]
        else:
            value = dash.no_update
    else:
        value = regions[:4]
    return (
        value,
        options,
        "Comparison of libraries",
    )

@app.callback(
    [
        Output("measure-select", "value"),
        Output("measure-select", "options"),
        Output("map-title", "children"),
    ],
    [Input("measure-select-all", "value"), Input("state-select", "value"),],
)
def update_measure_dropdown(select_all, state_select):
    state_raw_data = data_dict[state_select]
    measures = ['source', 'rank', 'depencies', 'dependants']

    ctx = dash.callback_context
    if ctx.triggered[0]["prop_id"].split(".")[0] == "measure-select-all":
        if select_all == ["All"]:
            value = [i["value"] for i in options]
        else:
            value = dash.no_update
    else:
        value = measures[:4]
    return (
        value,
        options,
        "Comparison of libraries",
    )


@app.callback(
    Output("library-checklist-container", "children"),
    [Input("region-select", "value")],
    [State("region-select", "options"), State("region-select-all", "value")],
)
def update_library_checklist(selected, select_options, checked):
    if len(selected) < len(select_options) and len(checked) == 0:
        raise PreventUpdate()

    elif len(selected) < len(select_options) and len(checked) == 1:
        return dcc.Checklist(
            id="region-select-all",
            options=[{"label": "Select All Regions", "value": "All"}],
            value=[],
            style={'display': 'None'},
        )

    elif len(selected) == len(select_options) and len(checked) == 1:
        raise PreventUpdate()

    return dcc.Checklist(
        id="region-select-all",
        options=[{"label": "Select All Regions", "value": "All"}],
        value=["All"],
        style={'display': 'None'},
    )

@app.callback(
    Output("neasure-checklist-container", "children"),
    [Input("measure-select", "value")],
    [State("measure-select", "options"), State("measure-select-all", "value")],
)
def update_measure_checklist(selected, select_options, checked):
    if len(selected) < len(select_options) and len(checked) == 0:
        raise PreventUpdate()

    elif len(selected) < len(select_options) and len(checked) == 1:
        return dcc.Checklist(
            id="measure-select-all",
            options=[{"label": "Select All Measures", "value": "All"}],
            value=[],
            style={'display': 'None'},
        )

    elif len(selected) == len(select_options) and len(checked) == 1:
        raise PreventUpdate()

    return dcc.Checklist(
        id="measure-select-all",
        options=[{"label": "Select All Measures", "value": "All"}],
        value=["All"],
    )


@app.callback(
    Output("cost-stats-container", "children"),
    [
        Input("geo-map", "selectedData"),
        Input("procedure-plot", "selectedData"),
        Input("metric-select", "value"),
        Input("state-select", "value"),
    ],
)
def update_hospital_datatable(geo_select, procedure_select, cost_select, state_select):
    state_agg = generate_aggregation(data_dict[state_select], cost_metric)
    state_agg = {
        "Name": [],
        "Description": [],
        "Lastest Release Version": [],
        "Lastest Release Date": [],
        "Col 5": [],
    }

    # make table from geo-select
    geo_data_dict = {
        "Name": [],
        "Description": [],
        "Lastest Release Version": [],
        "Lastest Release Date": [],
        "Col 5": [],
    }

    ctx = dash.callback_context
    if ctx.triggered:
        prop_id = ctx.triggered[0]["prop_id"].split(".")[0]

        # make table from procedure-select
        if prop_id == "procedure-plot" and procedure_select is not None:

            for point in procedure_select["points"]:
                provider = point["customdata"]

                dff = state_agg[state_agg["Name"] == provider]

                geo_data_dict["Name"].append(point["customdata"])
                city = dff["Hospital Referral Region (HRR) Description"].tolist()[0]
                geo_data_dict["Description"].append(city)

                address = dff["Provider Street Address"].tolist()[0]
                geo_data_dict["Lastest Release Version"].append(address)

                geo_data_dict["Lastest Release Date"].append(
                    dff[cost_select]["max"].tolist()[0]
                )
                geo_data_dict["Col 5"].append(
                    dff[cost_select]["min"].tolist()[0]
                )

        if prop_id == "geo-map" and geo_select is not None:

            for point in geo_select["points"]:
                provider = point["customdata"][0]
                dff = state_agg[state_agg["Name"] == provider]

                geo_data_dict["Name"].append(point["customdata"][0])
                geo_data_dict["Description"].append(point["customdata"][1].split("- ")[1])

                address = dff["Provider Street Address"].tolist()[0]
                geo_data_dict["Lastest Release Version"].append(address)

                geo_data_dict["Lastest Release Date"].append(
                    dff[cost_select]["max"].tolist()[0]
                )
                geo_data_dict["Col 5"].append(
                    dff[cost_select]["min"].tolist()[0]
                )

        geo_data_df = pd.DataFrame(data=geo_data_dict)
        data = geo_data_df.to_dict("rows")

    else:
        data = [{}]

    return dash_table.DataTable(
        id="cost-stats-table",
        columns=[{"name": i, "id": i} for i in geo_data_dict.keys()],
        data=data,
        filter_action="native",
        page_size=5,
        style_cell={"background-color": "#242a3b", "color": "#7b7d8d"},
        style_as_list_view=False,
        style_header={"background-color": "#1f2536", "padding": "0px 5px"},
    )


@app.callback(
    Output("procedure-stats-container", "children"),
    [
        Input("procedure-plot", "selectedData"),
        Input("geo-map", "selectedData"),
        Input("metric-select", "value"),
    ],
    [State("state-select", "value")],
)
def update_procedure_stats(procedure_select, geo_select, cost_select, state_select):
    procedure_dict = {
        "Rank": [],
        "Stars": [],
        "Dependent Repos": [],
        "Dependents": [],
    }

    ctx = dash.callback_context
    prop_id = ""
    if ctx.triggered:
        prop_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if prop_id == "procedure-plot" and procedure_select is not None:
        for point in procedure_select["points"]:
            procedure_dict["DRG"].append(point["y"].split(" - ")[0])
            procedure_dict["Procedure"].append(point["y"].split(" - ")[1])

            procedure_dict["Provider Name"].append(point["customdata"])
            procedure_dict["Cost Summary"].append(("${:,.2f}".format(point["x"])))

    # Display all procedures at selected hospital
    provider_select = []

    if prop_id == "geo-map" and geo_select is not None:
        for point in geo_select["points"]:
            provider = point["customdata"][0]
            provider_select.append(provider)

        state_raw_data = data_dict[state_select]
        provider_filtered = state_raw_data[
            state_raw_data["Provider Name"].isin(provider_select)
        ]

        for i in range(len(provider_filtered)):
            procedure_dict["DRG"].append(
                provider_filtered.iloc[i]["DRG Definition"].split(" - ")[0]
            )
            procedure_dict["Procedure"].append(
                provider_filtered.iloc[i]["DRG Definition"].split(" - ")[1]
            )
            procedure_dict["Provider Name"].append(
                provider_filtered.iloc[i]["Provider Name"]
            )
            procedure_dict["Cost Summary"].append(
                "${:,.2f}".format(provider_filtered.iloc[0][cost_select])
            )

    procedure_data_df = pd.DataFrame(data=procedure_dict)

    return dash_table.DataTable(
        id="procedure-stats-table",
        columns=[{"name": i, "id": i} for i in procedure_dict.keys()],
        data=procedure_data_df.to_dict("rows"),
        filter_action="native",
        sort_action="native",
        style_cell={
            "textOverflow": "ellipsis",
            "background-color": "#242a3b",
            "color": "#7b7d8d",
        },
        sort_mode="multi",
        page_size=5,
        style_as_list_view=False,
        style_header={"background-color": "#1f2536", "padding": "2px 12px 0px 12px"},
    )


@app.callback(
    Output("geo-map", "figure"),
    [
        Input("metric-select", "value"),
        Input("region-select", "value"),
        Input("procedure-plot", "selectedData"),
        Input("state-select", "value"),
    ],
)
def update_geo_map(cost_select, region_select, procedure_select, state_select):
    # generate geo map from state-select, procedure-select
    state_agg_data = generate_aggregation(data_dict[state_select], cost_metric)

    provider_data = {"procedure": [], "hospital": []}
    if procedure_select is not None:
        for point in procedure_select["points"]:
            provider_data["procedure"].append(point["y"])
            provider_data["hospital"].append(point["customdata"])

    return generate_geo_map(state_agg_data, cost_select, region_select, provider_data)


@app.callback(
    Output("procedure-plot", "figure"),
    [
        Input("metric-select", "value"),
        Input("region-select", "value"),
        Input("geo-map", "selectedData"),
        Input("state-select", "value"),
    ],
)
def update_procedure_plot(cost_select, region_select, geo_select, state_select):
    # generate procedure plot from selected provider
    state_raw_data = data_dict[state_select]

    provider_select = []
    if geo_select is not None:
        for point in geo_select["points"]:
            provider_select.append(point["customdata"][0])
    return generate_procedure_plot(
        state_raw_data, cost_select, region_select, provider_select
    )


if __name__ == "__main__":
    app.run_server(host='0.0.0.0', debug=True, port=8050)