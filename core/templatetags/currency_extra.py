from django import template
from django.conf import settings

register = template.Library()

@register.filter
def kes(value):
    if value is None:
        return 'KSh 0.00'
    try:
        return f'KSh {float(value):,.2f}'
    except (ValueError, TypeError):
        return 'KSh 0.00'

@register.simple_tag
def currency_symbol():
    return getattr(settings, 'CURRENCY', 'KES')

@register.filter
def ksh(value):
    """Kenya Shillings format"""
    if value is None:
        return 'KSh 0.00'
    try:
        return f'KSh {float(value):,.2f}'
    except (ValueError, TypeError):
        return 'KSh 0.00'