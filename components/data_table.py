# IMPORTANT: Always include the following imports as shown
from dash import callback, html, dcc, Output, Input
import dash_design_kit as ddk
import dash_ag_grid as dag
import pandas as pd
import numpy as np
import sys
import traceback
import os

from data import get_data
from components.filter_component import filter_data, FILTER_CALLBACK_INPUTS
from logger import logger


def component():
    '''Return a component with an Ag-Grid table displaying filtered data'''
    layout = ddk.Card(
        id="data_table",  # CRITICAL: use id that matches the component filename (without .py extension)
        children=[
            ddk.CardHeader(title="Flight Data Table"),
            html.Div(id="data_table_title", style={"padding": "10px", "fontWeight": "bold"}),
            # Add the Ag-Grid component
            dag.AgGrid(
                id="data_table_grid",
                columnDefs=[],
                dashGridOptions={
                    "pagination": True,
                    "paginationPageSize": 50,
                    "domLayout": "normal",
                    "rowSelection": "multiple",
                    "defaultColDef": {
                        "sortable": True,
                        "filter": True,
                        "resizable": True,
                        "floatingFilter": True
                    },
                    # Ensure clean table styling - no zebra striping
                    "rowStyle": {"backgroundColor": "#FFFFFF"},
                    "getRowStyle": None,  # Disable any alternating row colors
                    "suppressRowHoverHighlight": False,
                    "headerHeight": 40,
                    "rowHeight": 38
                },
                # Style to ensure clean borders and no striping
                style={"height": "600px", "width": "100%"},
                className="ag-theme-alpine",
                # empty rowData will be filled by callback
                rowData=[]
            ),
            # Use title attribute for the footer text
            ddk.CardFooter(title="Full flight data table with filtering, sorting, and pagination capabilities. Limited to a maximum of 10,000 rows.")
        ],
        width=100  # Full width table
    )

    # Return a dictionary with the layout
    return {
        "layout": layout,
        "test_inputs": {}
    }

@callback(
    output=[
        Output("data_table_grid", "columnDefs"),
        Output("data_table_grid", "rowData"),
        Output("data_table_title", "children")
    ],
    # Global filters
    inputs=FILTER_CALLBACK_INPUTS
)
def update(**kwargs):  # IMPORTANT - Keep this call signature as **kwargs, do not change or expand this.
    '''Update the data table based on filters and controls'''
    try:
        logger.debug("Starting data table update")
        
        # Get data and apply filters
        df = filter_data(get_data(), **kwargs)  # returns pandas dataframe
        
        logger.debug(f"Filtered data shape: {df.shape}")

        if len(df) == 0:
            return [], [], "No data available after filtering"

        # Limit to top 10,000 rows to prevent performance issues
        original_count = len(df)
        df = df.head(10_000)
        
        # Create title with row count information
        if original_count > 10_000:
            title = f"Showing 10,000 of {original_count:,} rows (limited for performance)"
        else:
            title = f"Showing {len(df):,} rows"

        # Create column definitions based on dataframe columns
        column_defs = []
        
        # Define important columns to display first
        priority_columns = ['date', 'airline_name', 'flight', 'origin', 'dest', 'dep_time', 'arr_time', 
                          'dep_delay', 'arr_delay', 'on_time', 'delay_category', 'distance']
        
        # Add priority columns first
        for col in priority_columns:
            if col in df.columns:
                col_def = {
                    "headerName": col.replace('_', ' ').title(),
                    "field": col,
                    "filter": True,
                    "sortable": True
                }

                # Add specific formatting for different column types
                if col == 'date':
                    col_def["valueFormatter"] = {"function": "d3.timeFormat('%Y-%m-%d')(new Date(params.value))"}
                elif col in ['dep_delay', 'arr_delay']:
                    col_def["type"] = "numericColumn"
                    col_def["filter"] = "agNumberColumnFilter"
                    col_def["cellStyle"] = {"function": "params.value > 15 ? {'color': 'red'} : params.value < 0 ? {'color': 'green'} : {}"}
                elif col in ['dep_time', 'arr_time', 'sched_dep_time', 'sched_arr_time']:
                    col_def["type"] = "numericColumn"
                    col_def["filter"] = "agNumberColumnFilter"
                    col_def["valueFormatter"] = {"function": "Math.floor(params.value/100) + ':' + (params.value%100).toString().padStart(2, '0')"}
                elif col == 'on_time':
                    col_def["cellRenderer"] = {"function": "params.value ? '✓ On Time' : '✗ Delayed'"}
                    col_def["cellStyle"] = {"function": "params.value ? {'color': 'green'} : {'color': 'red'}"}
                elif pd.api.types.is_numeric_dtype(df[col]):
                    col_def["type"] = "numericColumn"
                    col_def["filter"] = "agNumberColumnFilter"
                elif pd.api.types.is_string_dtype(df[col]):
                    col_def["filter"] = "agTextColumnFilter"

                column_defs.append(col_def)

        # Add remaining columns
        for col in df.columns:
            if col not in priority_columns and not col.startswith('_') and col != 'index':
                col_def = {
                    "headerName": col.replace('_', ' ').title(),
                    "field": col,
                    "filter": True,
                    "sortable": True
                }

                if pd.api.types.is_datetime64_any_dtype(df[col]):
                    col_def["valueFormatter"] = {"function": "d3.timeFormat('%Y-%m-%d')(new Date(params.value))"}
                elif pd.api.types.is_numeric_dtype(df[col]):
                    col_def["type"] = "numericColumn"
                    col_def["filter"] = "agNumberColumnFilter"
                elif pd.api.types.is_string_dtype(df[col]):
                    col_def["filter"] = "agTextColumnFilter"

                column_defs.append(col_def)

        logger.debug(f"Created {len(column_defs)} column definitions")

        # Clean the data and ensure proper format for Ag-Grid
        df_cleaned = df.copy()
        
        for col in df_cleaned.columns:
            # Replace empty strings with np.nan for numeric columns
            if pd.api.types.is_numeric_dtype(df_cleaned[col]):
                df_cleaned[col] = df_cleaned[col].replace('', np.nan)
        
        # Convert to dictionary records with proper NaN handling
        row_data = df_cleaned.to_dict('records')

        # Handle NaN values properly
        for row in row_data:
            for key, value in row.items():
                if pd.isna(value):  # CORRECT: Use pd.isna() - NEVER use pd.NaType!
                    row[key] = None

        logger.debug(f"Prepared {len(row_data)} rows for display")

        return column_defs, row_data, title

    except Exception as e:
        logger.debug(f"Error updating data table: {e}")
        print(f"Error updating data table: {e}, {traceback.format_exc()}")
        return [], [], f"Error loading data: {str(e)}"
