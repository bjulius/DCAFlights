from dash import callback, html, dcc, Output, Input
import dash_design_kit as ddk
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import sys
import os
import traceback

from data import get_data
from components.filter_component import filter_data, FILTER_CALLBACK_INPUTS
from logger import logger

def component():
    # Component ID
    component_id = "flight_connections_map"

    # Graph and error IDs
    graph_id = f"{component_id}_graph"
    error_id = f"{component_id}_error"
    loading_id = f"{component_id}_loading"

    # Get data to populate control options
    df = get_data()
    
    # Airline control
    airline_control_id = f"{component_id}_airline"
    airline_options = [{"label": "All Airlines", "value": "all"}]
    unique_airlines = df['airline_name'].dropna().replace('', np.nan).dropna().unique().tolist()
    airline_options.extend([{"label": str(airline), "value": airline} for airline in sorted(unique_airlines) if airline is not None and str(airline).strip()])
    airline_default = "all"

    # Time period control
    time_period_control_id = f"{component_id}_time_period"
    time_period_options = [{"label": "All Time Periods", "value": "all"}]
    unique_periods = df['time_period'].dropna().replace('', np.nan).dropna().unique().tolist()
    time_period_options.extend([{"label": str(period), "value": period} for period in sorted(unique_periods) if period is not None and str(period).strip()])
    time_period_default = "all"

    # Title and description
    title = "Flight Connections Map"
    description = "Interactive map showing direct flight connections from DCA airport with curved flight lines, filtered by airline and time periods"

    # Create the component layout
    layout = ddk.Card(
        id=component_id,
        children=[
            ddk.CardHeader(
                title=title
            ),
            # Add the controls with horizontal flexbox layout
            html.Div(
                style={"display": "flex", "flexDirection": "row", "flexWrap": "wrap", "rowGap": "10px", "alignItems": "center", "marginBottom": "15px"},
                children=[
                    # Airline dropdown control
                    html.Div(
                        children=[
                            html.Label("Airline:", style={"marginBottom": "5px", "fontWeight": "bold", "display": "block"}),
                            dcc.Dropdown(
                                id=airline_control_id,
                                options=airline_options,
                                value=airline_default,
                                style={"minWidth": "200px"}
                            )
                        ],
                        style={"display": "flex", "flexDirection": "column", "marginRight": "15px"}
                    ),
                    # Time period dropdown control
                    html.Div(
                        children=[
                            html.Label("Time Period:", style={"marginBottom": "5px", "fontWeight": "bold", "display": "block"}),
                            dcc.Dropdown(
                                id=time_period_control_id,
                                options=time_period_options,
                                value=time_period_default,
                                style={"minWidth": "200px"}
                            )
                        ],
                        style={"display": "flex", "flexDirection": "column", "marginRight": "15px"}
                    ),
                ],
            ),
            # Add the graph with loading indicator
            dcc.Loading(
                id=loading_id,
                type="circle",
                children=[
                    ddk.Graph(id=graph_id),
                ]
            ),
            # Add error message container to display errors
            html.Pre(id=error_id, style={"color": "red", "margin": "10px 0"}),
            # Use title attribute for the footer text
            ddk.CardFooter(title=description)
        ],
        width=50
    )

    # Create test inputs dictionary
    test_inputs = {
        airline_control_id: {
            "options": [option["value"] for option in airline_options],
            "default": airline_default
        },
        time_period_control_id: {
            "options": [option["value"] for option in time_period_options],
            "default": time_period_default
        }
    }

    # Return both the layout and test inputs
    return {
        "layout": layout,
        "test_inputs": test_inputs
    }

@callback(
    output=[
        Output("flight_connections_map_graph", "figure"),
        Output("flight_connections_map_error", "children")
    ],
    inputs={
        # Chart-specific controls
        'flight_connections_map_airline': Input("flight_connections_map_airline", "value"),
        'flight_connections_map_time_period': Input("flight_connections_map_time_period", "value"),

        # Global filters
        **FILTER_CALLBACK_INPUTS
    }
)
def update(**kwargs):
    # Create an empty figure as fallback
    empty_fig = go.Figure()
    empty_fig.update_layout(
        title="No data available",
        annotations=[{
            "text": "No data is available to display",
            "showarrow": False,
            "font": {"size": 20}
        }]
    )

    try:
        # Get the data and apply filters
        df = filter_data(get_data(), **kwargs)
        if len(df) == 0:
            return empty_fig, ""

        # Extract chart-specific control values from kwargs
        selected_airline = kwargs.get('flight_connections_map_airline', 'all')
        selected_time_period = kwargs.get('flight_connections_map_time_period', 'all')

        # Apply additional filters based on controls
        if selected_airline != 'all':
            df = df[df['airline_name'] == selected_airline]
        
        if selected_time_period != 'all':
            df = df[df['time_period'] == selected_time_period]

        if len(df) == 0:
            return empty_fig, "No flights found for the selected filters"

        logger.debug("Starting chart creation. df:\n%s", df.head())

        # Airport coordinates (approximate)
        airport_coords = {
            'DCA': {'lat': 38.8512, 'lon': -77.0402, 'name': 'Washington Reagan National'},
            'ABQ': {'lat': 35.0402, 'lon': -106.6091, 'name': 'Albuquerque'},
            'AUS': {'lat': 30.1945, 'lon': -97.6699, 'name': 'Austin'},
            'BUF': {'lat': 42.9405, 'lon': -78.7322, 'name': 'Buffalo'},
            'CHS': {'lat': 32.8986, 'lon': -80.0405, 'name': 'Charleston'},
            'CMH': {'lat': 39.9980, 'lon': -82.8919, 'name': 'Columbus'},
            'DFW': {'lat': 32.8968, 'lon': -97.0380, 'name': 'Dallas Fort Worth'},
            'GEG': {'lat': 47.6198, 'lon': -117.5336, 'name': 'Spokane'},
            'GSP': {'lat': 34.8957, 'lon': -82.2189, 'name': 'Greenville-Spartanburg'},
            'MCO': {'lat': 28.4294, 'lon': -81.3089, 'name': 'Orlando'},
            'MSP': {'lat': 44.8848, 'lon': -93.2223, 'name': 'Minneapolis'},
            'ORD': {'lat': 41.9786, 'lon': -87.9048, 'name': 'Chicago O\'Hare'},
            'ROC': {'lat': 43.1189, 'lon': -77.6724, 'name': 'Rochester'},
            'SEA': {'lat': 47.4502, 'lon': -122.3088, 'name': 'Seattle'},
            'SYR': {'lat': 43.1111, 'lon': -76.1063, 'name': 'Syracuse'},
            'TPA': {'lat': 27.9755, 'lon': -82.5332, 'name': 'Tampa'},
            'TUS': {'lat': 32.1161, 'lon': -110.9411, 'name': 'Tucson'}
        }

        # Get unique destinations and flight counts
        dest_counts = df.groupby(['dest', 'airline_name']).size().reset_index(name='flight_count')
        
        # Create the map figure
        fig = go.Figure()

        # Add destination airports as markers
        for dest in dest_counts['dest'].unique():
            if dest in airport_coords:
                dest_data = dest_counts[dest_counts['dest'] == dest]
                total_flights = dest_data['flight_count'].sum()
                
                fig.add_trace(go.Scattermap(
                    lat=[airport_coords[dest]['lat']],
                    lon=[airport_coords[dest]['lon']],
                    mode='markers',
                    marker=dict(
                        size=max(8, min(30, total_flights / 5)),  # Scale marker size by flight count
                        color='red'
                    ),
                    text=[f"{airport_coords[dest]['name']} ({dest})<br>Total Flights: {total_flights}"],
                    hovertemplate="%{text}<extra></extra>",
                    name=f"{dest} Airport",
                    showlegend=False
                ))

        # Add origin airport (DCA)
        fig.add_trace(go.Scattermap(
            lat=[airport_coords['DCA']['lat']],
            lon=[airport_coords['DCA']['lon']],
            mode='markers',
            marker=dict(size=20, color='blue'),
            text=[f"{airport_coords['DCA']['name']} (DCA)<br>Origin Airport"],
            hovertemplate="%{text}<extra></extra>",
            name="DCA (Origin)",
            showlegend=False
        ))

        # Add flight paths as curved lines
        lat_coords = []
        lon_coords = []
        
        for dest in dest_counts['dest'].unique():
            if dest in airport_coords:
                # Origin coordinates
                origin_lat = airport_coords['DCA']['lat']
                origin_lon = airport_coords['DCA']['lon']
                
                # Destination coordinates
                dest_lat = airport_coords[dest]['lat']
                dest_lon = airport_coords[dest]['lon']
                
                # Create curved path by adding intermediate points
                num_points = 50
                lats = np.linspace(origin_lat, dest_lat, num_points)
                lons = np.linspace(origin_lon, dest_lon, num_points)
                
                # Add curvature by offsetting the middle points
                mid_point = num_points // 2
                lat_offset = (dest_lat - origin_lat) * 0.2
                lon_offset = (dest_lon - origin_lon) * 0.2
                
                for i in range(num_points):
                    curve_factor = np.sin(np.pi * i / (num_points - 1))
                    lats[i] += lat_offset * curve_factor
                    lons[i] += lon_offset * curve_factor
                
                # Add coordinates to the main arrays with None separators
                lat_coords.extend(lats.tolist())
                lat_coords.append(None)
                lon_coords.extend(lons.tolist())
                lon_coords.append(None)

        # Add all flight paths as a single trace for better performance
        if lat_coords and lon_coords:
            fig.add_trace(go.Scattermap(
                lat=lat_coords,
                lon=lon_coords,
                mode='lines',
                line=dict(width=2, color='rgba(255, 0, 0, 0.6)'),
                connectgaps=False,
                hoverinfo='skip',
                name="Flight Paths",
                showlegend=False
            ))

        # Update layout for the map
        fig.update_layout(
            map=dict(
                style="open-street-map",
                center=dict(lat=39.0, lon=-95.0),  # Center on US
                zoom=3
            ),
            margin=dict(l=0, r=0, t=0, b=0),
            height=600
        )

        return fig, ""

    except Exception as e:
        error_msg = f"Error updating chart: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        empty_fig.update_layout(
            title="Error in chart",
            annotations=[{"text": "An error occurred while updating this chart", "showarrow": False, "font": {"size": 20}}]
        )
        return empty_fig, error_msg
