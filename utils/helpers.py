# utils/helpers.py
from datetime import datetime
import re


def extract_year_month_season(date_str):
    """
    Extract the first (year, month) from a date string
    and return the corresponding season.
    """

    match = re.search(r'([A-Za-z]{3})\s+\d{1,2},\s*(\d{4})', date_str)
    if not match:
        return None

    month_str, year = match.groups()
    month = datetime.strptime(month_str, "%b").month

    season = get_season(month)

    return int(year), season


def get_season(month):
    if month in (12, 1, 2):
        return "winter"
    elif month in (3, 4, 5):
        return "spring"
    elif month in (6, 7, 8):
        return "summer"
    else:
        return "autumn"
