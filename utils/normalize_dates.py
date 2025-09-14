from dateutil import parser as date_parser
from datetime import datetime, timedelta
import re
import pytz

def normalize_date(date_str):
    """
    Converts various date formats from RSS, FinancialExpress, or EconomicTimes into a consistent
    ISO 8601 UTC format without microseconds.
    Returns: ISO 8601 UTC string (e.g., '2025-07-12T10:30:00+00:00') or empty string if failed.
    """
    try:
        # Case 1: RSS format — e.g., "Sat, 12 Jul 2025 16:03:43 +0530"
        if "," in date_str and "+" in date_str:
            dt = date_parser.parse(date_str)

        # Case 2: Financial Express — e.g., "July 11, 2025 21:59 IST"
        elif "IST" in date_str:
            date_str = date_str.replace("IST", "+05:30")
            dt = date_parser.parse(date_str)

        # Case 3: Relative — e.g., "1 Hour ago", "3 days ago"
        elif re.match(r"[\d\.]+\s+(minute|hour|day|week)s?\s+ago", date_str.lower()):
            match = re.match(r"([\d\.]+)\s+(minute|hour|day|week)s?\s+ago", date_str.lower())
            value = float(match.group(1))  # support decimals like 20.5
            unit = match.group(2)
            now = datetime.now(pytz.UTC)
            if unit == "minute":
                dt = now - timedelta(minutes=value)
            elif unit == "hour":
                dt = now - timedelta(hours=value)
            elif unit == "day":
                dt = now - timedelta(days=value)
            elif unit == "week":
                dt = now - timedelta(weeks=value)
        
        # Case 4: Groww format — e.g., "4 hours", "16 hours", "2 days"
        elif re.match(r"\d+\s+(minute|hour|day|week)s?$", date_str.lower()):
            match = re.match(r"(\d+)\s+(minute|hour|day|week)s?$", date_str.lower())
            value = int(match.group(1))
            unit = match.group(2)
            now = datetime.now(pytz.UTC)
            if unit == "minute":
                dt = now - timedelta(minutes=value)
            elif unit == "hour":
                dt = now - timedelta(hours=value)
            elif unit == "day":
                dt = now - timedelta(days=value)
            elif unit == "week":
                dt = now - timedelta(weeks=value)

        # Fallback: try parsing anything else
        else:
            dt = date_parser.parse(date_str)

        # Normalize to UTC and drop microseconds
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=pytz.UTC)
        else:
            dt = dt.astimezone(pytz.UTC)

        return dt.replace(microsecond=0).isoformat()

    except Exception as e:
        print(f"❌ Failed to normalize date: {date_str} — {e}")
        return ""

if __name__ == "__main__":
    result = normalize_date("25.5 hours ago")
    print(result)