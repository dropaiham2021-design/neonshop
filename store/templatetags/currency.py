from decimal import Decimal
from django import template

register = template.Library()

@register.filter
def money_plain(cents):
    """
    Render cents as 150 or 149.99 with no currency symbol.
    Safe if cents is None/empty.
    """
    try:
        d = Decimal(cents) / Decimal(100)
    except Exception:
        return ""
    s = f"{d:.2f}"
    return s.rstrip("0").rstrip(".")
