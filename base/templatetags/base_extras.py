from decimal import Decimal, InvalidOperation

from django import template

# from ..get_xchange import convert_from
from ..models import CurrencyConversionRate

register = template.Library()


@register.filter
def add_dec(value: Decimal, arg: Decimal) -> Decimal:
    try:
        return Decimal(value) + Decimal(arg)
    except:
        return Decimal()


@register.filter
def mul(value: Decimal, arg: Decimal) -> Decimal:
    try:
        return Decimal(value) * Decimal(arg)
    except:
        return Decimal()


@register.filter
def usd(value):
    """Format value as USD."""
    try:
        if Decimal(value) < 0:
            return f"-US${abs(value):,.2f}"
        return f"US${value:,.2f}"
    except InvalidOperation:
        return None


@register.filter
def minus(x: Decimal, y: Decimal) -> Decimal:
    """
    x|minus:y = x - y
    """
    return x - y


@register.filter
def home_currency(value: Decimal, symbol: str) -> str:

    conversion_object, created = CurrencyConversionRate.objects.get_or_create(
        cfrom="USD", cto=symbol
    )
    rate = conversion_object.ccrate
    new_value = rate * value
    try:
        if Decimal(new_value) < 0:
            return f"-{symbol}{abs(new_value):,.2f}"
        return f"{symbol}{new_value:,.2f}"
    except InvalidOperation:
        return ""
