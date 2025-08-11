import json
import pandas as pd
import numpy as np
from logger import logger

def get_data(data_path='data/data.csv'):
    # Define explicit type mappings for all columns
    type_mapping = {
        # String columns (keep as strings initially)
        "month_name": str,
        "day_of_week": str,
        "carrier": str,
        "airline_name": str,
        "flight": str,
        "tailnum": str,
        "origin": str,
        "dest": str,
        "delay_category": str,
        "time_period": str,

        # Numeric columns (use nullable types for mixed data)
        "year": "Int64",
        "month": "Int64",
        "day": "Int64",
        "day_of_week_num": "Int64",
        "sched_dep_time": "Int64",
        "dep_time": "Int64",
        "dep_delay": "Int64",
        "dep_delay_flag": "Int64",
        "sched_arr_time": "Int64",
        "arr_time": "Int64",
        "arr_delay": "Int64",
        "arr_delay_flag": "Int64",
        "on_time": "Int64",
        "air_time": "Int64",
        "distance": "Int64",

        # Date/time columns (keep as strings initially for conversion)
        "date": str,
    }

    # Define column-specific values to treat as NaN (for mixed type columns)
    na_values_mapping = {}
    
    # Load data based on file extension
    if data_path.endswith('.parquet'):
        # Read Parquet files
        df = pd.read_parquet(data_path, engine='pyarrow')
    else:
        # Read CSV with explicit type mapping and column-specific na_values and automatic separator detection
        df = pd.read_csv(data_path, dtype=type_mapping, na_values=na_values_mapping, sep=None)
    
    logger.debug("Data loaded. Shape: %s", df.shape)
    logger.debug("Sample data:\n%s", df.head())

    # Date conversions - don't assume dates are already in datetime format!
    # Based on sample data: "2022-03-22" (ISO format)
    df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d')

    # Create boolean versions of flag columns
    df['dep_delay_flag_bool'] = df['dep_delay_flag'] == 1
    df['arr_delay_flag_bool'] = df['arr_delay_flag'] == 1
    df['on_time_bool'] = df['on_time'] == 1

    logger.debug("Data after transformations:\n%s", df.head())

    # Filter out rows where all values are null
    df = df.dropna(how='all')

    return df
