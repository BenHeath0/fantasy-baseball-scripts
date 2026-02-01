"""Utility functions for fantasy baseball player evaluation"""

import pandas as pd
from datetime import datetime
import os
from .config import DATA_REFRESH_DAYS, LAST_FETCHED_FILE, INPUT_DATA_DIR


def cleanup_juniors(df, key):
    """Remove 'Jr.' from player names and clean whitespace"""
    df[key] = df[key].str.replace("Jr.", "", regex=False).str.strip()
    return df


def determine_fetch_needed():
    """Check if we need to fetch new data based on last fetch date"""
    try:
        with open(LAST_FETCHED_FILE, "r") as file:
            last_fetched_str = file.read().strip()
            if not last_fetched_str:
                return True
            last_fetched = datetime.strptime(last_fetched_str, "%Y-%m-%d %H:%M:%S")
            if (datetime.now() - last_fetched).days >= DATA_REFRESH_DAYS:
                return True
    except FileNotFoundError:
        return True

    return False


def update_last_fetched():
    """Update the last fetched timestamp"""
    with open(LAST_FETCHED_FILE, "w") as file:
        file.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


def ensure_directory_exists(directory):
    """Create directory if it doesn't exist"""
    if not os.path.exists(directory):
        os.makedirs(directory)


def safe_float_conversion(value, default=0.0):
    """Safely convert value to float, return default if conversion fails"""
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default


def get_current_date_string():
    """Get current date as string in YYYY-MM-DD format"""
    return datetime.now().strftime("%Y-%m-%d")


def load_local_csv_data(filename):
    """Load CSV data from input_data directory with error handling"""
    filepath = f"{INPUT_DATA_DIR}/{filename}"
    try:
        return pd.read_csv(filepath)
    except FileNotFoundError:
        print(f"Warning: {filepath} not found. This data will be skipped.")
        return None
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return None
