from django import template
from datetime import datetime, timedelta

register = template.Library()

@register.filter
def add_months(value, months):
    """Add a number of months to a date string (approximate)"""
    try:
        date = datetime.strptime(value, '%Y/%m/%d')
        # Approximate month addition (30 days per month)
        days_to_add = int(months) * 30
        new_date = date + timedelta(days=days_to_add)
        return new_date.strftime('%Y/%m/%d')
    except (ValueError, TypeError):
        return value 