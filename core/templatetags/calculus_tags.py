from decimal import Decimal, InvalidOperation

from django import template

from core.constants import STATES
from core.gst import money, plain

register = template.Library()


@register.filter
def inr(value):
    """1234567.5 -> ₹12,34,567.50"""
    try:
        v = money(Decimal(str(value)))
    except (InvalidOperation, ValueError):
        return ""
    sign = "-" if v < 0 else ""
    whole, frac = f"{abs(v):.2f}".split(".")
    if len(whole) > 3:
        head, tail, parts = whole[:-3], whole[-3:], []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        whole = ",".join(parts + [tail])
    return f"{sign}\u20b9{whole}.{frac}"


@register.filter
def num(value):
    return plain(value)


@register.filter
def state_name(code):
    return STATES.get(code, code)
