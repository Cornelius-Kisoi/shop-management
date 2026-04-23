from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView, TemplateView
from django.shortcuts import redirect
from users.urls import urlpatterns as users_urls
from users.views_django import login_view, logout_view, register_view
from products.urls import urlpatterns as products_urls
from customers.urls import urlpatterns as customers_urls
from sales.urls import urlpatterns as sales_urls
from reports.urls import urlpatterns as reports_urls
from django.contrib.auth import views as auth_views

def dashboard_redirect(request):
    return redirect('/reports/summary/')

def health_check(request):
    from django.db import connection
    from django.core.cache import cache
    from django.http import JsonResponse
    import time

    health_data = {
        'status': 'healthy',
        'timestamp': time.time(),
        'checks': {}
    }

    # Database check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_data['checks']['database'] = 'healthy'
    except Exception as e:
        health_data['checks']['database'] = f'unhealthy: {str(e)}'
        health_data['status'] = 'unhealthy'

    # Cache check
    try:
        cache.set('health_check', 'ok', 10)
        if cache.get('health_check') == 'ok':
            health_data['checks']['cache'] = 'healthy'
        else:
            health_data['checks']['cache'] = 'unhealthy: cache not working'
            health_data['status'] = 'unhealthy'
    except Exception as e:
        health_data['checks']['cache'] = f'unhealthy: {str(e)}'
        health_data['status'] = 'unhealthy'

    return JsonResponse(health_data)

def maintenance_mode(request):
    return TemplateView.as_view(template_name='maintenance.html')(request)

urlpatterns = [
    path('', RedirectView.as_view(url='/accounts/login/', permanent=False), name='home'),
    path('admin/', admin.site.urls),
    path('health/', health_check, name='health_check'),
    path('maintenance/', maintenance_mode, name='maintenance'),
    path('admin/logout/', lambda r: redirect('/accounts/logout/')),
    path('accounts/login/', login_view, name='login'),
    path('accounts/register/', register_view, name='register'),
    path('accounts/logout/', logout_view, name='logout'),
    path('dashboard/', dashboard_redirect, name='dashboard'),
    path('offline.html', TemplateView.as_view(template_name='offline.html'), name='offline'),
    path('api/users/', include(users_urls)),
    path('api/products/', include(products_urls)),
    path('api/customers/', include(customers_urls)),
    path('api/sales/', include(sales_urls)),
    path('api/reports/', include(reports_urls)),
    path('api/', include('shopmanagement.api_urls')),
    path('products/', include('products.urls_django')),
    path('sales/', include('sales.urls_django')),
    path('customers/', include('customers.urls_django')),
    path('reports/', include('reports.urls_django')),
    path('users/', include('users.urls_django')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)