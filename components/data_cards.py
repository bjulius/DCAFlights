# IMPORTANT: Always include the following imports as shown
from dash import callback, html, dcc, Output, Input
import dash_design_kit as ddk
import numpy as np
import pandas as pd
import sys
import traceback
import os

from data import get_data
from components.filter_component import filter_data, FILTER_CALLBACK_INPUTS
from logger import logger

def component():
    '''Return a component with data cards displaying key metrics'''
    layout = ddk.Row(
        id="data_cards",
        children=[
            ddk.DataCard(
                id='total_flights_card',
                value='...',
                label='Total Flights',
                width=20
            ),
            ddk.DataCard(
                id='avg_delay_card',
                value='...',
                label='Avg Arrival Delay (min)',
                width=20
            ),
            ddk.DataCard(
                id='on_time_rate_card',
                value='...',
                label='On-Time Rate (%)',
                width=20
            ),
            ddk.DataCard(
                id='avg_distance_card',
                value='...',
                label='Avg Distance (miles)',
                width=20
            ),
            ddk.DataCard(
                id='max_delay_card',
                value='...',
                label='Max Delay (min)',
                width=20
            )
        ])

    # Return a dictionary with the layout
    return {
        "layout": layout,
        "test_inputs": {}
    }

@callback(
    [
        Output('total_flights_card', 'value'),
        Output('avg_delay_card', 'value'),
        Output('on_time_rate_card', 'value'),
        Output('avg_distance_card', 'value'),
        Output('max_delay_card', 'value')
    ],
    # IMPORTANT - Do not add any additional inputs here
    FILTER_CALLBACK_INPUTS
)
def update(**kwargs):  # IMPORTANT - Keep this as **kwargs
    '''Update all data cards with the filtered data metrics'''
    try:
        logger.debug("Starting data cards update")
        
        # Get data and apply filters
        df = filter_data(get_data(), **kwargs)  # returns pandas dataframe
        
        logger.debug(f"Filtered data shape: {df.shape}")

        # Check if dataframe is empty
        if len(df) == 0:
            logger.debug("No data after filtering")
            return ["No Data", "No Data", "No Data", "No Data", "No Data"]

        # Calculate metrics based on the filtered data
        total_flights = len(df)
        avg_delay = df["arr_delay"].mean()
        on_time_rate = (df["on_time"].sum() / len(df)) * 100
        avg_distance = df["distance"].mean()
        max_delay = df["arr_delay"].max()

        logger.debug(f"Calculated metrics - Total: {total_flights}, Avg delay: {avg_delay:.1f}, On-time: {on_time_rate:.1f}%")

        # Format the results
        total_flights_formatted = f"{total_flights:,}"
        avg_delay_formatted = f"{avg_delay:.1f}"
        on_time_rate_formatted = f"{on_time_rate:.1f}%"
        avg_distance_formatted = f"{avg_distance:,.0f}"
        max_delay_formatted = f"{max_delay}"

        return [total_flights_formatted, avg_delay_formatted, on_time_rate_formatted, avg_distance_formatted, max_delay_formatted]
    except Exception as e:
        logger.debug(f"Error updating data cards: {e}")
        print(f"Error updating data cards: {e}\n{traceback.format_exc()}")
        return ["Error", "Error", "Error", "Error", "Error"]
