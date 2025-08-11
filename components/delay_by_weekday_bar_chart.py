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
    component_id = "delay_by_weekday_bar_chart"

    # Graph and error IDs
    graph_id = f"{component_id}_graph"
    error_id = f"{component_id}_error"
    loading_id = f"{component_id}_loading"

    # Delay type dropdown control
    delay_type_id = f"{component_id}_delay_type"
    delay_type_options = [
        {"label": "Departure Delay", "value": "dep_delay"},
        {"label": "Arrival Delay", "value": "arr_delay"}
    ]
    delay_type_default = "dep_delay"

    # Delayed flights only checkbox
    delayed_only_id = f"{component_id}_delayed_only"

    # Title and description
    title = "Average Delay by Day of Week"
    description = "Bar chart showing average flight delays by day of the week with options to toggle between departure and arrival delays and filter to delayed flights only."

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
                    # Delay type dropdown
                    html.Div(
                        children=[
                            html.Label("Delay Type:", style={"marginBottom": "5px", "fontWeight": "bold", "display": "block"}),
                            dcc.Dropdown(
                                id=delay_type_id,
                                options=delay_type_options,
                                value=delay_type_default,
                                style={"minWidth": "200px"}
                            )
                        ],
                        style={"display": "flex", "flexDirection": "column", "marginRight": "15px"}
                    ),
                    # Delayed flights only checkbox
                    html.Div(
                        children=[
                            html.Label("Filter Options:", style={"marginBottom": "5px", "fontWeight": "bold", "display": "block"}),
                            dcc.Checklist(
                                id=delayed_only_id,
                                options=[{"label": "Delayed flights only", "value": "enabled"}],
                                value=[],
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
        delay_type_id: {
            "options": [option["value"] for option in delay_type_options],
            "default": delay_type_default
        },
        delayed_only_id: {
            "options": [[], ["enabled"]],
            "default": []
        }
    }

    # Return both the layout and test inputs
    return {
        "layout": layout,
        "test_inputs": test_inputs
    }

@callback(
    output=[
        Output(f"delay_by_weekday_bar_chart_graph", "figure"),
        Output(f"delay_by_weekday_bar_chart_error", "children")
    ],
    inputs={
        # Chart-specific controls
        'delay_by_weekday_bar_chart_delay_type': Input("delay_by_weekday_bar_chart_delay_type", "value"),
        'delay_by_weekday_bar_chart_delayed_only': Input("delay_by_weekday_bar_chart_delayed_only", "value"),

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
        delay_type = kwargs.get('delay_by_weekday_bar_chart_delay_type', 'dep_delay')
        delayed_only = kwargs.get('delay_by_weekday_bar_chart_delayed_only', [])

        logger.debug("Starting chart creation. df shape: %s, delay_type: %s, delayed_only: %s", df.shape, delay_type, delayed_only)

        # Filter to delayed flights only if checkbox is checked
        if 'enabled' in delayed_only:
            if delay_type == 'dep_delay':
                df = df[df['dep_delay'] > 0].copy()
            else:  # arr_delay
                df = df[df['arr_delay'] > 0].copy()

        if len(df) == 0:
            return empty_fig, "No delayed flights found after filtering"

        # Ensure delay column is numeric
        df[delay_type] = pd.to_numeric(df[delay_type], errors='coerce')
        
        # Remove any rows with null delay values
        df = df.dropna(subset=[delay_type])

        if len(df) == 0:
            return empty_fig, "No valid delay data found"

        # Define day of week order for proper chronological sorting
        day_order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        
        # Group by day of week and calculate average delay
        avg_delay = df.groupby('day_of_week')[delay_type].mean().reset_index()
        
        # Ensure all days are present and in correct order
        avg_delay['day_of_week'] = pd.Categorical(avg_delay['day_of_week'], categories=day_order, ordered=True)
        avg_delay = avg_delay.sort_values('day_of_week')

        logger.debug("Processed data for chart:\n%s", avg_delay.head())

        # Create bar chart
        fig = px.bar(
            avg_delay,
            x='day_of_week',
            y=delay_type,
            title=""
        )

        # Update layout
        delay_label = "Departure Delay" if delay_type == 'dep_delay' else "Arrival Delay"
        filter_text = " (Delayed Flights Only)" if 'enabled' in delayed_only else ""
        
        fig.update_layout(
            xaxis_title="Day of Week",
            yaxis_title=f"Average {delay_label} (minutes)",
            showlegend=False,
            # Add subtle gridlines
            xaxis=dict(
                gridcolor='#EEEEEE',
                gridwidth=1,
                showgrid=True
            ),
            yaxis=dict(
                gridcolor='#EEEEEE', 
                gridwidth=1,
                showgrid=True
            ),
            plot_bgcolor='white',
            paper_bgcolor='white'
        )

        # Update hover template
        fig.update_traces(
            hovertemplate=f"<b>%{{x}}</b><br>Average {delay_label}: %{{y:.1f}} minutes<extra></extra>"
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
