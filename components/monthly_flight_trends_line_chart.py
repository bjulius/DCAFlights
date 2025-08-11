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
from statsmodels.tsa.seasonal import seasonal_decompose

from data import get_data
from components.filter_component import filter_data, FILTER_CALLBACK_INPUTS
from logger import logger

def component():
    # Component ID
    component_id = "monthly_flight_trends_line_chart"

    # Graph and error IDs
    graph_id = f"{component_id}_graph"
    error_id = f"{component_id}_error"
    loading_id = f"{component_id}_loading"

    # Metric dropdown control
    metric_control_id = f"{component_id}_metric"
    metric_options = [
        {"label": "Flight Count", "value": "flight_count"},
        {"label": "Average Departure Delay", "value": "avg_dep_delay"},
        {"label": "On-Time Percentage", "value": "on_time_pct"}
    ]
    metric_default = "flight_count"

    # Year range slider control
    year_slider_id = f"{component_id}_year_range"
    year_min = 2019
    year_max = 2024
    year_default = [2019, 2024]

    # Title and description
    title = "Monthly Flight Trends with Time Series Decomposition"
    description = "Monthly flight volume and delay trends with time series decomposition showing trend, seasonal, and residual components"

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
                    # Metric dropdown control
                    html.Div(
                        children=[
                            html.Label("Metric:", style={"marginBottom": "5px", "fontWeight": "bold", "display": "block"}),
                            dcc.Dropdown(
                                id=metric_control_id,
                                options=metric_options,
                                value=metric_default,
                                style={"minWidth": "200px"}
                            )
                        ],
                        style={"display": "flex", "flexDirection": "column", "marginRight": "15px"}
                    ),
                    # Year range slider control
                    html.Div(
                        children=[
                            html.Label("Year Range:", style={"marginBottom": "5px", "fontWeight": "bold", "display": "block"}),
                            html.Div(
                                children=dcc.RangeSlider(
                                    id=year_slider_id,
                                    min=year_min,
                                    max=year_max,
                                    step=1,
                                    value=year_default,
                                    marks={
                                        int(2019): "2019",
                                        int(2020): "2020",
                                        int(2021): "2021",
                                        int(2022): "2022",
                                        int(2023): "2023",
                                        int(2024): "2024"
                                    },
                                    tooltip={"placement": "bottom", "always_visible": True}
                                ),
                                style={"minWidth": "300px"}
                            )
                        ],
                        style={"display": "flex", "flexDirection": "column", "marginRight": "15px", "width": "400px"}
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
        width=100
    )

    # Create test inputs dictionary
    test_inputs = {
        metric_control_id: {
            "options": [option["value"] for option in metric_options],
            "default": metric_default
        },
        year_slider_id: {
            "options": [[2019, 2024], [2020, 2023], [2021, 2022]],
            "default": year_default
        }
    }

    return {
        "layout": layout,
        "test_inputs": test_inputs
    }

@callback(
    output=[
        Output("monthly_flight_trends_line_chart_graph", "figure"),
        Output("monthly_flight_trends_line_chart_error", "children")
    ],
    inputs={
        # Chart-specific controls
        'monthly_flight_trends_line_chart_metric': Input("monthly_flight_trends_line_chart_metric", "value"),
        'monthly_flight_trends_line_chart_year_range': Input("monthly_flight_trends_line_chart_year_range", "value"),

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
        metric = kwargs.get('monthly_flight_trends_line_chart_metric', 'flight_count')
        year_range = kwargs.get('monthly_flight_trends_line_chart_year_range', [2019, 2024])

        # Filter by year range
        df = df[(df['year'] >= year_range[0]) & (df['year'] <= year_range[1])]
        
        if len(df) == 0:
            return empty_fig, ""

        # Create year-month column for grouping
        df['year_month'] = df['year'].astype(str) + '-' + df['month'].astype(str).str.zfill(2)
        df['date_month'] = pd.to_datetime(df['year_month'], format='%Y-%m')

        # Group by month and calculate metrics
        monthly_data = df.groupby(['year_month', 'date_month']).agg({
            'flight': 'count',
            'dep_delay': 'mean',
            'on_time': 'mean'
        }).reset_index()

        monthly_data.columns = ['year_month', 'date_month', 'flight_count', 'avg_dep_delay', 'on_time_pct']
        monthly_data['on_time_pct'] = monthly_data['on_time_pct'] * 100  # Convert to percentage

        # Sort by date
        monthly_data = monthly_data.sort_values('date_month')

        logger.debug("Starting chart creation. monthly_data:\n%s", monthly_data.head())

        # Check if we have enough data points for decomposition (need at least 2 full years)
        if len(monthly_data) < 24:
            # Create simple line chart without decomposition
            if metric == 'flight_count':
                y_values = monthly_data['flight_count']
                y_title = "Flight Count"
            elif metric == 'avg_dep_delay':
                y_values = monthly_data['avg_dep_delay']
                y_title = "Average Departure Delay (minutes)"
            else:  # on_time_pct
                y_values = monthly_data['on_time_pct']
                y_title = "On-Time Percentage (%)"

            fig = px.line(
                monthly_data,
                x='date_month',
                y=y_values,
                title=f"Monthly {y_title}"
            )
            
            fig.update_layout(
                xaxis_title="Month",
                yaxis_title=y_title,
                height=400,
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
            
            return fig, ""

        # Perform time series decomposition
        if metric == 'flight_count':
            ts_data = monthly_data.set_index('date_month')['flight_count']
            y_title = "Flight Count"
        elif metric == 'avg_dep_delay':
            ts_data = monthly_data.set_index('date_month')['avg_dep_delay']
            y_title = "Average Departure Delay (minutes)"
        else:  # on_time_pct
            ts_data = monthly_data.set_index('date_month')['on_time_pct']
            y_title = "On-Time Percentage (%)"

        # Perform seasonal decomposition
        decomposition = seasonal_decompose(ts_data, model='additive', period=12)

        # Create subplots
        from plotly.subplots import make_subplots
        
        fig = make_subplots(
            rows=4, cols=1,
            subplot_titles=[
                f"Original {y_title}",
                "Trend Component",
                "Seasonal Component", 
                "Residual Component"
            ],
            vertical_spacing=0.08,
            shared_xaxes=True
        )

        # Original data
        fig.add_trace(
            go.Scatter(
                x=ts_data.index,
                y=ts_data.values,
                mode='lines+markers',
                name='Original',
                line={"color": "#5470c6"}  # Use new colorway
            ),
            row=1, col=1
        )

        # Trend component
        fig.add_trace(
            go.Scatter(
                x=decomposition.trend.index,
                y=decomposition.trend.values,
                mode='lines',
                name='Trend',
                line={"color": "#FF6600"}  # Neon orange
            ),
            row=2, col=1
        )

        # Seasonal component
        fig.add_trace(
            go.Scatter(
                x=decomposition.seasonal.index,
                y=decomposition.seasonal.values,
                mode='lines',
                name='Seasonal',
                line={"color": "#39FF14"}  # Neon green
            ),
            row=3, col=1
        )

        # Residual component
        fig.add_trace(
            go.Scatter(
                x=decomposition.resid.index,
                y=decomposition.resid.values,
                mode='lines',
                name='Residual',
                line={"color": "#ee6666"}  # Use new colorway
            ),
            row=4, col=1
        )

        # Update layout
        fig.update_layout(
            height=800,
            showlegend=False,
            title_text=f"Time Series Decomposition: {y_title}",
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
        
        # Update all axes to have subtle gridlines
        fig.update_xaxes(gridcolor='#EEEEEE', gridwidth=1, showgrid=True)
        fig.update_yaxes(gridcolor='#EEEEEE', gridwidth=1, showgrid=True)

        # Update x-axis for bottom subplot only
        fig.update_xaxes(title_text="Month", row=4, col=1)

        # Update y-axes
        fig.update_yaxes(title_text=y_title, row=1, col=1)
        fig.update_yaxes(title_text="Trend", row=2, col=1)
        fig.update_yaxes(title_text="Seasonal", row=3, col=1)
        fig.update_yaxes(title_text="Residual", row=4, col=1)

        return fig, ""

    except Exception as e:
        error_msg = f"Error updating chart: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        empty_fig.update_layout(
            title="Error in chart",
            annotations=[{"text": "An error occurred while updating this chart", "showarrow": False, "font": {"size": 20}}]
        )
        return empty_fig, error_msg
