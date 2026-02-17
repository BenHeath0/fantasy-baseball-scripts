"""Utility functions for fantasy baseball player evaluation"""

import pandas as pd
import re
import unicodedata
from datetime import datetime
import os
from .config import INPUT_DATA_DIR


def normalize_player_name(name):
    """Standardize a player name for consistent merging across data sources.

    Strips diacritics, removes suffixes (Jr., Sr., II-V), removes periods,
    removes single-letter middle initials, and collapses whitespace.
    """
    if not isinstance(name, str):
        return name
    # Strip diacritics: decompose then remove combining characters
    name = unicodedata.normalize("NFD", name)
    name = "".join(c for c in name if unicodedata.category(c) != "Mn")
    # Remove suffixes at end of name
    name = re.sub(r"\s+(Jr|Sr|III|II|IV|V)\.?\s*$", "", name)
    # Remove periods and apostrophes
    name = name.replace(".", "").replace("'", "")
    # Remove single-letter middle initials (e.g., "Luis L Ortiz" -> "Luis Ortiz")
    name = re.sub(r"\b([A-Z])\s(?=[A-Z])", "", name)
    # Collapse whitespace and strip
    name = " ".join(name.split())
    return name


def normalize_name_column(df, col="player_name"):
    """Apply normalize_player_name to a DataFrame column in-place."""
    df[col] = df[col].apply(normalize_player_name)
    return df


def safe_float_conversion(value, default=0.0):
    """Safely convert value to float, return default if conversion fails"""
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default


def load_local_csv_data(filename):
    """Load CSV/TSV data from input_data directory with error handling"""
    filepath = f"{INPUT_DATA_DIR}/{filename}"
    try:
        if filename.endswith(".tsv"):
            return pd.read_csv(filepath, sep="\t")
        return pd.read_csv(filepath)
    except FileNotFoundError:
        print(f"Warning: {filepath} not found. This data will be skipped.")
        return None
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return None
