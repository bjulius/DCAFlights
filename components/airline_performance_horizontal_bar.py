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
    component_id = "airline_performance_horizontal_bar"

    # Graph and error IDs
    graph_id = f"{component_id}_graph"
    error_id = f"{component_id}_error"
    loading_id = f"{component_id}_loading"

    # Sort control
    sort_control_id = f"{component_id}_sort"
    sort_options = [
        {"label": "On-Time Percentage", "value": "on_time_pct"},
        {"label": "Total Flights", "value": "total_flights"}
    ]
    sort_default = "on_time_pct"

    # Delay category filter control
    delay_filter_id = f"{component_id}_delay_filter"
    delay_options = [
        {"label": "Early/On-Time", "value": "Early/On-Time"},
        {"label": "Slightly Late", "value": "Slightly Late"},
        {"label": "Delayed", "value": "Delayed"},
        {"label": "Severely Delayed", "value": "Severely Delayed"}
    ]
    delay_default = ["Early/On-Time", "Slightly Late", "Delayed", "Severely Delayed"]

    # Title and description
    title = "Airline On-Time Performance Comparison"
    description = "Horizontal bar chart comparing airline performance by on-time percentage or total flights, with filtering by delay categories"

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
                    # Sort by dropdown
                    html.Div(
                        children=[
                            html.Label("Sort By:", style={"marginBottom": "5px", "fontWeight": "bold", "display": "block"}),
                            dcc.Dropdown(
                                id=sort_control_id,
                                options=sort_options,
                                value=sort_default,
                                style={"minWidth": "200px"}
                            )
                        ],
                        style={"display": "flex", "flexDirection": "column", "marginRight": "15px"}
                    ),
                    # Delay category filter
                    html.Div(
                        children=[
                            html.Label("Delay Categories:", style={"marginBottom": "5px", "fontWeight": "bold", "display": "block"}),
                            dcc.Dropdown(
                                id=delay_filter_id,
                                options=delay_options,
                                value=delay_default,
                                multi=True,
                                style={"minWidth": "300px"}
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
        sort_control_id: {
            "options": [option["value"] for option in sort_options],
            "default": sort_default
        },
        delay_filter_id: {
            "options": [option["value"] for option in delay_options],
            "default": delay_default
        }
    }

    # Return both the layout and test inputs
    return {
        "layout": layout,
        "test_inputs": test_inputs
    }

@callback(
    output=[
        Output("airline_performance_horizontal_bar_graph", "figure"),
        Output("airline_performance_horizontal_bar_error", "children")
    ],
    inputs={
        # Chart-specific controls
        'airline_performance_horizontal_bar_sort': Input("airline_performance_horizontal_bar_sort", "value"),
        'airline_performance_horizontal_bar_delay_filter': Input("airline_performance_horizontal_bar_delay_filter", "value"),

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
        sort_by = kwargs.get('airline_performance_horizontal_bar_sort', 'on_time_pct')
        delay_categories = kwargs.get('airline_performance_horizontal_bar_delay_filter', ["Early/On-Time", "Slightly Late", "Delayed", "Severely Delayed"])

        # Ensure delay_categories is a list
        if not isinstance(delay_categories, list):
            delay_categories = [delay_categories] if delay_categories else []

        # Filter by selected delay categories
        if delay_categories:
            df = df[df['delay_category'].isin(delay_categories)]

        if len(df) == 0:
            return empty_fig, "No data available for selected delay categories"

        logger.debug("Starting chart creation. df:\n%s", df.head())

        # Calculate airline performance metrics
        airline_stats = df.groupby('airline_name').agg({
            'on_time': ['sum', 'count'],
            'flight': 'count'
        }).reset_index()

        # Flatten column names
        airline_stats.columns = ['airline_name', 'on_time_flights', 'total_flights', 'total_flights_check']
        
        # Calculate on-time percentage
        airline_stats['on_time_pct'] = (airline_stats['on_time_flights'] / airline_stats['total_flights'] * 100).round(1)

        # Sort based on user selection
        if sort_by == 'on_time_pct':
            airline_stats = airline_stats.sort_values('on_time_pct', ascending=True)
            x_col = 'on_time_pct'
            x_title = "On-Time Percentage (%)"
            hover_template = "<b>%{y}</b><br>On-Time: %{x:.1f}%<br>Total Flights: %{customdata[0]}<extra></extra>"
            custom_data = [airline_stats['total_flights']]
        else:
            airline_stats = airline_stats.sort_values('total_flights', ascending=True)
            x_col = 'total_flights'
            x_title = "Total Flights"
            hover_template = "<b>%{y}</b><br>Total Flights: %{x}<br>On-Time: %{customdata[0]:.1f}%<extra></extra>"
            custom_data = [airline_stats['on_time_pct']]

        # Create horizontal bar chart
        fig = px.bar(
            airline_stats,
            x=x_col,
            y='airline_name',
            orientation='h',
            custom_data=custom_data
        )

        # Update traces for better styling
        fig.update_traces(
            hovertemplate=hover_template
        )

        # Update layout
        fig.update_layout(
            xaxis_title=x_title,
            yaxis_title="Airline",
            showlegend=False,
            height=max(400, len(airline_stats) * 40)  # Dynamic height based on number of airlines
        )

        # Update axes
        fig.update_yaxes(categoryorder="array", categoryarray=airline_stats['airline_name'].tolist())

        return fig, ""

    except Exception as e:
        error_msg = f"Error updating chart: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        empty_fig.update_layout(
            title="Error in chart",
            annotations=[{"text": "An error occurred while updating this chart", "showarrow": False, "font": {"size": 20}}]
        )
        return empty_fig, error_msg
