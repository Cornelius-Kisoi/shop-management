from django.conf import settings

def currency_processor(request):
    return {
        'currency': getattr(settings, 'CURRENCY', 'KES'),
        'currency_symbol': 'KES '
    }