from django.conf import settings

def currency(request):
    return {
        'currency': getattr(settings, 'CURRENCY', 'KES'),
    }