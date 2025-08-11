from dash import callback, html, dcc, Output, Input
import dash_design_kit as ddk
import numpy as np
import pandas as pd
import sys
import os
from datetime import datetime, time

from data import get_data
from logger import logger

class FILTER_COMPONENT_IDS:
    year_filter = "year_filter"
    airline_filter = "airline_filter"
    destination_airport_filter = "destination_airport_filter"
    month_filter = "month_filter"
    day_of_week_filter = "day_of_week_filter"
    time_period_filter = "time_period_filter"
    delay_category_filter = "delay_category_filter"
    flight_distance_min = "flight_distance_min"
    flight_distance_max = "flight_distance_max"
    date_range_filter = "date_range_filter"


FILTER_CALLBACK_INPUTS = {
    "year": Input(FILTER_COMPONENT_IDS.year_filter, "value"),
    "airline": Input(FILTER_COMPONENT_IDS.airline_filter, "value"),
    "destination_airport": Input(FILTER_COMPONENT_IDS.destination_airport_filter, "value"),
    "month": Input(FILTER_COMPONENT_IDS.month_filter, "value"),
    "day_of_week": Input(FILTER_COMPONENT_IDS.day_of_week_filter, "value"),
    "time_period": Input(FILTER_COMPONENT_IDS.time_period_filter, "value"),
    "delay_category": Input(FILTER_COMPONENT_IDS.delay_category_filter, "value"),
    "flight_distance_min": Input(FILTER_COMPONENT_IDS.flight_distance_min, "value"),
    "flight_distance_max": Input(FILTER_COMPONENT_IDS.flight_distance_max, "value"),
    "date_start": Input(FILTER_COMPONENT_IDS.date_range_filter, "start_date"),
    "date_end": Input(FILTER_COMPONENT_IDS.date_range_filter, "end_date"),
}


def component():
    df = get_data()

    logger.debug("Filter component data loaded. Shape: %s", df.shape)
    logger.debug("Filter component sample data:\n%s", df.head())

    # Get unique values for dropdowns
    unique_years = sorted(df["year"].unique().tolist())
    unique_airlines = sorted(df["airline_name"].unique().tolist())
    unique_destinations = sorted(df["dest"].unique().tolist())
    unique_months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    unique_days_of_week = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    unique_time_periods = sorted(df["time_period"].unique().tolist())
    unique_delay_categories = sorted(df["delay_category"].unique().tolist())

    # Compute min/max for flight distance
    distance_min = df["distance"].min()
    distance_max = df["distance"].max()

    # start/end dates
    start_date = df["date"].min()
    end_date = df["date"].max()

    layout = html.Div([ddk._ControlPanel(
        position="top",
        default_open=True,
        control_groups=[
            {
                "title": "Filters",
                "id": "filter_control_group",
                "description": "",
                "children": [
                    html.Div(
                        children=dcc.Dropdown(
                            id=FILTER_COMPONENT_IDS.year_filter,
                            options=[{"label": "All", "value": "all"}] + [{"label": str(y), "value": y} for y in unique_years],
                            multi=True,
                            value=["all"]
                        ),
                        id=FILTER_COMPONENT_IDS.year_filter + "_parent",
                        title="Year",
                        style={"minWidth": "200px"}
                    ),

                    html.Div(
                        children=dcc.Dropdown(
                            id=FILTER_COMPONENT_IDS.airline_filter,
                            options=[{"label": "All", "value": "all"}] + [{"label": a, "value": a} for a in unique_airlines],
                            multi=True,
                            value=["all"]
                        ),
                        id=FILTER_COMPONENT_IDS.airline_filter + "_parent",
                        title="Airline",
                        style={"minWidth": "200px"}
                    ),

                    html.Div(
                        children=dcc.Dropdown(
                            id=FILTER_COMPONENT_IDS.destination_airport_filter,
                            options=[{"label": "All", "value": "all"}] + [{"label": d, "value": d} for d in unique_destinations],
                            multi=True,
                            value=["all"]
                        ),
                        id=FILTER_COMPONENT_IDS.destination_airport_filter + "_parent",
                        title="Destination Airport",
                        style={"minWidth": "200px"}
                    ),

                    html.Div(
                        children=dcc.Dropdown(
                            id=FILTER_COMPONENT_IDS.month_filter,
                            options=[{"label": "All", "value": "all"}] + [{"label": m, "value": m} for m in unique_months],
                            multi=True,
                            value=["all"]
                        ),
                        id=FILTER_COMPONENT_IDS.month_filter + "_parent",
                        title="Month",
                        style={"minWidth": "200px"}
                    ),

                    html.Div(
                        children=dcc.Dropdown(
                            id=FILTER_COMPONENT_IDS.day_of_week_filter,
                            options=[{"label": "All", "value": "all"}] + [{"label": d, "value": d} for d in unique_days_of_week],
                            multi=True,
                            value=["all"]
                        ),
                        id=FILTER_COMPONENT_IDS.day_of_week_filter + "_parent",
                        title="Day of Week",
                        style={"minWidth": "200px"}
                    ),

                    html.Div(
                        children=dcc.Dropdown(
                            id=FILTER_COMPONENT_IDS.time_period_filter,
                            options=[{"label": "All", "value": "all"}] + [{"label": t, "value": t} for t in unique_time_periods],
                            multi=True,
                            value=["all"]
                        ),
                        id=FILTER_COMPONENT_IDS.time_period_filter + "_parent",
                        title="Time Period",
                        style={"minWidth": "200px"}
                    ),

                    html.Div(
                        children=dcc.Dropdown(
                            id=FILTER_COMPONENT_IDS.delay_category_filter,
                            options=[{"label": "All", "value": "all"}] + [{"label": d, "value": d} for d in unique_delay_categories],
                            multi=True,
                            value=["all"]
                        ),
                        id=FILTER_COMPONENT_IDS.delay_category_filter + "_parent",
                        title="Delay Category",
                        style={"minWidth": "200px"}
                    ),

                    html.Div(
                        children=html.Div([
                            dcc.Input(id=FILTER_COMPONENT_IDS.flight_distance_min, value=distance_min, debounce=True, style={"width": 100}),
                            html.Span(" - ", style={"margin": "0 8px", "alignSelf": "center"}),
                            dcc.Input(id=FILTER_COMPONENT_IDS.flight_distance_max, value=distance_max, debounce=True, style={"width": 100})
                        ], style={
                            "display": "flex",
                            "alignItems": "center",
                            "flexWrap": "wrap"
                        }),
                        title="Flight Distance (miles)"
                    ),

                    html.Div(
                        children=dcc.DatePickerRange(
                            id=FILTER_COMPONENT_IDS.date_range_filter,
                            start_date_placeholder_text="Start Date",
                            end_date_placeholder_text="End Date",
                            start_date=start_date,
                            end_date=end_date,
                        ),
                        id=FILTER_COMPONENT_IDS.date_range_filter + "_parent",
                        title="Date Range"
                    ),
                ],
            },
        ],
    ), html.Div(id='total_results', style={ 'paddingTop': 20, 'marginLeft': 50, 'fontStyle': 'italic', 'minHeight': 45 })])

    test_inputs = {
        "year": {
            "options": ["all"] + unique_years[:3],
            "default": ["all"]
        },
        "airline": {
            "options": ["all"] + unique_airlines[:3],
            "default": ["all"]
        },
        "destination_airport": {
            "options": ["all"] + unique_destinations[:3],
            "default": ["all"]
        },
        "month": {
            "options": ["all"] + unique_months[:3],
            "default": ["all"]
        },
        "day_of_week": {
            "options": ["all"] + unique_days_of_week[:3],
            "default": ["all"]
        },
        "time_period": {
            "options": ["all"] + unique_time_periods[:3],
            "default": ["all"]
        },
        "delay_category": {
            "options": ["all"] + unique_delay_categories[:3],
            "default": ["all"]
        },
        "flight_distance_min": {
            "options": [distance_min, (distance_min + distance_max) / 2, distance_max],
            "default": distance_min
        },
        "flight_distance_max": {
            "options": [distance_max, (distance_min + distance_max) / 2, distance_min],
            "default": distance_max
        },
        "date_start": {
            "options": [start_date.strftime("%Y-%m-%d") if hasattr(start_date, "strftime") else start_date],
            "default": start_date.strftime("%Y-%m-%d") if hasattr(start_date, "strftime") else start_date
        },
        "date_end": {
            "options": [end_date.strftime("%Y-%m-%d") if hasattr(end_date, "strftime") else end_date],
            "default": end_date.strftime("%Y-%m-%d") if hasattr(end_date, "strftime") else end_date
        }
    }

    return {
        "layout": layout,
        "test_inputs": test_inputs
    }

def filter_data(df, **filters):
    logger.debug("Starting data filtering. Original shape: %s", df.shape)
    logger.debug("Applied filters: %s", filters)

    df = df.copy()

    # Year filter
    if len(filters["year"]) > 0 and "all" not in filters["year"]:
        df = df[df["year"].isin(filters["year"])]

    # Airline filter
    if len(filters["airline"]) > 0 and "all" not in filters["airline"]:
        df = df[df["airline_name"].isin(filters["airline"])]

    # Destination airport filter
    if len(filters["destination_airport"]) > 0 and "all" not in filters["destination_airport"]:
        df = df[df["dest"].isin(filters["destination_airport"])]

    # Month filter - need to map month names to month_name column
    if len(filters["month"]) > 0 and "all" not in filters["month"]:
        df = df[df["month_name"].isin(filters["month"])]

    # Day of week filter
    if len(filters["day_of_week"]) > 0 and "all" not in filters["day_of_week"]:
        df = df[df["day_of_week"].isin(filters["day_of_week"])]

    # Time period filter
    if len(filters["time_period"]) > 0 and "all" not in filters["time_period"]:
        df = df[df["time_period"].isin(filters["time_period"])]

    # Delay category filter
    if len(filters["delay_category"]) > 0 and "all" not in filters["delay_category"]:
        df = df[df["delay_category"].isin(filters["delay_category"])]

    # Flight distance range filter
    if "distance" in df.columns:
        df = df[df["distance"] >= float(filters["flight_distance_min"])]
        df = df[df["distance"] <= float(filters["flight_distance_max"])]

    # Date range filter
    if filters["date_start"] is not None:
        try:
            start_date = pd.to_datetime(filters["date_start"])
            df = df[df["date"] >= start_date]
        except (ValueError, TypeError):
            try:
                start_date = datetime.fromisoformat(filters["date_start"])
                df = df[df["date"] >= start_date]
            except (ValueError, TypeError) as e:
                logger.warning("Could not parse start_date filter: %s. Error: %s", filters["date_start"], e)

    if filters["date_end"] is not None:
        try:
            end_date = pd.to_datetime(filters["date_end"])
            df = df[df["date"] <= end_date]
        except (ValueError, TypeError):
            try:
                end_date = datetime.fromisoformat(filters["date_end"])
                df = df[df["date"] <= end_date]
            except (ValueError, TypeError) as e:
                logger.warning("Could not parse end_date filter: %s. Error: %s", filters["date_end"], e)

    logger.debug("Filtering complete. Final shape: %s", df.shape)
    logger.debug("Filtered data sample:\n%s", df.head())

    return df


@callback(Output("total_results", "children"), inputs=FILTER_CALLBACK_INPUTS)
def display_count(**kwargs):
    df = get_data()
    # Get total count
    count = len(df)

    filtered_df = filter_data(df, **kwargs)
    # Get filtered count
    filtered_count = len(filtered_df)

    return f"{filtered_count:,} / {count:,} rows"