"""Utility functions for the news scraper."""
from datetime import datetime
from typing import Optional
import re

def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse a date string into a datetime object.
    
    Args:
        date_str: Date string to parse, can be None
        
    Returns:
        Parsed datetime object or None if parsing fails
    """
    if not date_str:
        return None
        
    # Try common date formats
    date_formats = [
        '%Y-%m-%dT%H:%M:%S%z',  # ISO format with timezone
        '%Y-%m-%dT%H:%M:%S',    # ISO format without timezone
        '%Y-%m-%d %H:%M:%S',    # Common datetime format
        '%Y-%m-%d',             # Just date
        '%B %d, %Y',            # Month name, day, year
        '%d %B %Y',             # Day, month name, year
        '%Y/%m/%d',             # Date with slashes
        '%d/%m/%Y',             # Date with slashes (UK format)
        '%m/%d/%Y',             # Date with slashes (US format)
    ]
    
    # Clean up the date string
    date_str = date_str.strip()
    
    # Try each format
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
            
    # Try to extract date using regex
    # Look for patterns like "2 days ago", "5 hours ago", etc.
    time_ago_match = re.search(r'(\d+)\s+(second|minute|hour|day|week|month|year)s?\s+ago', date_str, re.I)
    if time_ago_match:
        amount = int(time_ago_match.group(1))
        unit = time_ago_match.group(2).lower()
        
        now = datetime.now()
        if unit == 'second':
            return now.replace(second=now.second - amount)
        elif unit == 'minute':
            return now.replace(minute=now.minute - amount)
        elif unit == 'hour':
            return now.replace(hour=now.hour - amount)
        elif unit == 'day':
            return now.replace(day=now.day - amount)
        elif unit == 'week':
            return now.replace(day=now.day - (amount * 7))
        elif unit == 'month':
            return now.replace(month=now.month - amount)
        elif unit == 'year':
            return now.replace(year=now.year - amount)
            
    return None
