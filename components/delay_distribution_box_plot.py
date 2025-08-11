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
    component_id = "delay_distribution_box_plot"

    # Graph and error IDs
    graph_id = f"{component_id}_graph"
    error_id = f"{component_id}_error"
    loading_id = f"{component_id}_loading"

    # Get data to determine available time periods
    df = get_data()
    available_periods = sorted(df['time_period'].dropna().unique().tolist())

    # Time period multi-select control
    time_period_id = f"{component_id}_time_periods"
    time_period_options = [{"label": period, "value": period}
                           for period in available_periods]
    time_period_default = available_periods  # Select all by default

    # Delay range slider control
    delay_range_id = f"{component_id}_delay_range"
    delay_min = -30
    delay_max = 120
    delay_default = [delay_min, delay_max]
    delay_marks = {
        int(-30): "-30",
        int(-15): "-15",
        int(0): "0",
        int(30): "30",
        int(60): "60",
        int(90): "90",
        int(120): "120"
    }

    # Title and description
    title = "Flight Delay Distribution by Time Period"
    description = "Box plot showing the distribution of arrival delays across different time periods of the day. Use controls to filter by specific time periods and delay ranges."

    # Create the component layout
    layout = ddk.Card(
        id=component_id,
        children=[
            ddk.CardHeader(
                title=title
            ),
            # Add the controls with horizontal flexbox layout
            html.Div(
                style={
                    "display": "flex",
                    "flexDirection": "row",
                    "flexWrap": "wrap",
                    "rowGap": "10px",
                    "alignItems": "center",
                    "marginBottom": "15px"},
                children=[
                    # Time period multi-select dropdown
                    html.Div(
                        children=[
                            html.Label(
                                "Time Periods:",
                                style={
                                    "marginBottom": "5px",
                                    "fontWeight": "bold",
                                    "display": "block"}),
                            dcc.Dropdown(
                                id=time_period_id,
                                options=time_period_options,
                                value=time_period_default,
                                multi=True,
                                style={"minWidth": "300px"}
                            )
                        ],
                        style={
                            "display": "flex",
                            "flexDirection": "column",
                            "marginRight": "15px"}
                    ),
                    # Delay range slider
                    html.Div(
                        children=[
                            html.Label(
                                "Delay Range (minutes):",
                                style={
                                    "marginBottom": "5px",
                                    "fontWeight": "bold",
                                    "display": "block"}),
                            html.Div(
                                children=dcc.RangeSlider(
                                    id=delay_range_id,
                                    min=delay_min,
                                    max=delay_max,
                                    step=5,
                                    value=delay_default,
                                    marks=delay_marks,
                                    tooltip={
                                        "placement": "bottom", "always_visible": True}
                                ),
                                style={"minWidth": "300px"}
                            )
                        ],
                        style={
                            "display": "flex",
                            "flexDirection": "column",
                            "marginRight": "15px",
                            "width": "400px"}
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
            ddk.CardFooter(title=description)
        ],
        width=50
    )

    # Create test inputs dictionary
    test_inputs = {
        time_period_id: {
            "options": available_periods,
            "default": available_periods
        },
        delay_range_id: {
            "options": [delay_min, delay_max],
            "default": delay_default
        }
    }

    return {
        "layout": layout,
        "test_inputs": test_inputs
    }


@callback(
    output=[
        Output("delay_distribution_box_plot_graph", "figure"),
        Output("delay_distribution_box_plot_error", "children")
    ],
    inputs={
        # Chart-specific controls
        'delay_distribution_box_plot_time_periods': Input("delay_distribution_box_plot_time_periods", "value"),
        'delay_distribution_box_plot_delay_range': Input("delay_distribution_box_plot_delay_range", "value"),

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
        selected_periods = kwargs.get(
            'delay_distribution_box_plot_time_periods', [])
        delay_range = kwargs.get(
            'delay_distribution_box_plot_delay_range', [-30, 120])

        # Ensure we have valid selections
        if not selected_periods:
            return empty_fig, "Please select at least one time period"

        # Convert delay range values to numeric
        delay_min_val = float(delay_range[0]) if delay_range and len(
            delay_range) >= 1 else -30
        delay_max_val = float(delay_range[1]) if delay_range and len(
            delay_range) >= 2 else 120

        # Filter by selected time periods
        df_filtered = df[df['time_period'].isin(selected_periods)].copy()

        if len(df_filtered) == 0:
            return empty_fig, "No data available for selected time periods"

        # Convert arr_delay to numeric and filter by delay range
        df_filtered['arr_delay'] = pd.to_numeric(
            df_filtered['arr_delay'], errors='coerce')
        df_filtered = df_filtered.dropna(subset=['arr_delay'])
        df_filtered = df_filtered[
            (df_filtered['arr_delay'] >= delay_min_val) &
            (df_filtered['arr_delay'] <= delay_max_val)
        ]

        if len(df_filtered) == 0:
            return empty_fig, f"No data available for delay range {delay_min_val} to {delay_max_val} minutes"

        logger.debug(
            "Starting chart creation. df_filtered shape: %s",
            df_filtered.shape)
        logger.debug(
            "Time periods in data: %s",
            df_filtered['time_period'].unique())
        logger.debug(
            "Delay range: %s to %s",
            df_filtered['arr_delay'].min(),
            df_filtered['arr_delay'].max())

        # Create box plot with jittered data points
        fig = px.box(
            df_filtered,
            x='time_period',
            y='arr_delay',
            points='all',
            category_orders={
                'time_period': [
                    'Early Morning',
                    'Morning',
                    'Afternoon',
                    'Evening',
                    'Night']}
        )

        # Update the jittered points to lighter blue, keep box plots default
        fig.update_traces(
            marker=dict(color='#87CEEB', size=5, opacity=0.6),  # Light blue for jittered points
            selector=dict(type='box')
        )

        # Update layout
        fig.update_layout(
            xaxis_title="Time Period",
            yaxis_title="Arrival Delay (minutes)",
            showlegend=False
        )

        # Add horizontal line at y=0 for reference
        fig.add_hline(
            y=0,
            line_dash="dash",
            line_color="gray",
            annotation_text="On Time",
            annotation_position="bottom right"
        )

        # Update hover template
        fig.update_traces(
            hovertemplate="<b>%{x}</b><br>Delay: %{y} minutes<extra></extra>"
        )

        return fig, ""

    except Exception as e:
        error_msg = f"Error updating chart: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        empty_fig.update_layout(
            title="Error in chart",
            annotations=[{"text": "An error occurred while updating this chart",
                          "showarrow": False, "font": {"size": 20}}]
        )
        return empty_fig, error_msg
