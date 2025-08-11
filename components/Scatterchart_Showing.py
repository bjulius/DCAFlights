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
    component_id = "Scatterchart_Showing"

    # Graph and error IDs
    graph_id = f"{component_id}_graph"
    error_id = f"{component_id}_error"
    loading_id = f"{component_id}_loading"

    # Color by control
    color_control_id = f"{component_id}_color"
    color_options = [
        {"label": "None", "value": "none"},
        {"label": "Airline", "value": "airline_name"},
        {"label": "Carrier", "value": "carrier"},
        {"label": "Delay Category", "value": "delay_category"},
        {"label": "Time Period", "value": "time_period"},
        {"label": "Day of Week", "value": "day_of_week"}
    ]
    color_default = "none"

    # Trendline control
    trendline_control_id = f"{component_id}_trendline"
    trendline_options = [
        {"label": "None", "value": "none"},
        {"label": "Linear (OLS)", "value": "ols"},
        {"label": "Lowess", "value": "lowess"}
    ]
    trendline_default = "ols"

    # Title and description
    title = "Departure vs Arrival Delay Analysis"
    description = "Scatter plot showing the relationship between departure delays and arrival delays with optional trendline analysis"

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
                    # Color by control
                    html.Div(
                        children=[
                            html.Label("Color By:", style={"marginBottom": "5px", "fontWeight": "bold", "display": "block"}),
                            dcc.Dropdown(
                                id=color_control_id,
                                options=color_options,
                                value=color_default,
                                style={"minWidth": "200px"}
                            )
                        ],
                        style={"display": "flex", "flexDirection": "column", "marginRight": "15px"}
                    ),
                    # Trendline control
                    html.Div(
                        children=[
                            html.Label("Trendline:", style={"marginBottom": "5px", "fontWeight": "bold", "display": "block"}),
                            dcc.Dropdown(
                                id=trendline_control_id,
                                options=trendline_options,
                                value=trendline_default,
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
        color_control_id: {
            "options": [option["value"] for option in color_options],
            "default": color_default
        },
        trendline_control_id: {
            "options": [option["value"] for option in trendline_options],
            "default": trendline_default
        }
    }

    # Return both the layout and test inputs
    return {
        "layout": layout,
        "test_inputs": test_inputs
    }

@callback(
    output=[
        Output("Scatterchart_Showing_graph", "figure"),
        Output("Scatterchart_Showing_error", "children")
    ],
    inputs={
        # Chart-specific controls
        'Scatterchart_Showing_color': Input("Scatterchart_Showing_color", "value"),
        'Scatterchart_Showing_trendline': Input("Scatterchart_Showing_trendline", "value"),

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
        color_by = kwargs.get('Scatterchart_Showing_color', "none")
        trendline_type = kwargs.get('Scatterchart_Showing_trendline', "ols")

        # Convert delay columns to numeric to ensure proper comparison
        df['dep_delay'] = pd.to_numeric(df['dep_delay'], errors='coerce')
        df['arr_delay'] = pd.to_numeric(df['arr_delay'], errors='coerce')

        # Remove rows with null delay values
        df = df.dropna(subset=['dep_delay', 'arr_delay'])

        if len(df) == 0:
            return empty_fig, "No valid delay data available after filtering"

        logger.debug("Starting chart creation. df shape: %s, dep_delay range: %s to %s, arr_delay range: %s to %s", 
                    df.shape, df['dep_delay'].min(), df['dep_delay'].max(), 
                    df['arr_delay'].min(), df['arr_delay'].max())

        # Create the scatter plot
        if color_by == "none" or color_by is None:
            # No color grouping
            if trendline_type == "none":
                fig = px.scatter(
                    df,
                    x="dep_delay",
                    y="arr_delay",
                    opacity=0.6,
                    hover_data=["flight", "airline_name", "dest"]
                )
            else:
                fig = px.scatter(
                    df,
                    x="dep_delay",
                    y="arr_delay",
                    trendline=trendline_type,
                    opacity=0.6,
                    hover_data=["flight", "airline_name", "dest"]
                )
        else:
            # With color grouping
            # Limit the number of categories for better visualization
            if color_by in df.columns:
                unique_values = df[color_by].value_counts()
                if len(unique_values) > 10:
                    # Keep top 9 categories and group the rest as "Other"
                    top_categories = unique_values.head(9).index.tolist()
                    df['color_column'] = df[color_by].apply(
                        lambda x: x if x in top_categories else 'Other'
                    )
                    color_column = 'color_column'
                else:
                    color_column = color_by

                if trendline_type == "none":
                    fig = px.scatter(
                        df,
                        x="dep_delay",
                        y="arr_delay",
                        color=color_column,
                        opacity=0.6,
                        hover_data=["flight", "airline_name", "dest"]
                    )
                else:
                    fig = px.scatter(
                        df,
                        x="dep_delay",
                        y="arr_delay",
                        color=color_column,
                        trendline=trendline_type,
                        opacity=0.6,
                        hover_data=["flight", "airline_name", "dest"]
                    )
            else:
                # Fallback if column doesn't exist
                fig = px.scatter(
                    df,
                    x="dep_delay",
                    y="arr_delay",
                    opacity=0.6,
                    hover_data=["flight", "airline_name", "dest"]
                )

        # Update layout
        fig.update_layout(
            xaxis_title="Departure Delay (minutes)",
            yaxis_title="Arrival Delay (minutes)",
            showlegend=True if color_by != "none" else False
        )

        # Add reference lines at zero
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
        fig.add_vline(x=0, line_dash="dash", line_color="gray", opacity=0.5)

        # Update hover template
        fig.update_traces(
            hovertemplate="<b>%{customdata[1]}</b><br>" +
                         "Flight: %{customdata[0]}<br>" +
                         "Destination: %{customdata[2]}<br>" +
                         "Departure Delay: %{x} min<br>" +
                         "Arrival Delay: %{y} min<extra></extra>"
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
