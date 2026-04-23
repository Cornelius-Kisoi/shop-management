from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from sales.models import Sale, SaleItem
from products.models import Product


@api_view(['GET'])
def api_root(request):
    return Response({
        'message': 'Shop Management API',
        'endpoints': {
            'users': '/api/users/',
            'products': '/api/products/',
            'customers': '/api/customers/',
            'sales': '/api/sales/',
            'reports': '/api/reports/',
        }
    })


class DashboardAPI(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        today = timezone.now().date()
        
        total_sales_today = Sale.objects.filter(created_at__date=today, status='completed').count()
        revenue_today = Sale.objects.filter(created_at__date=today, status='completed').aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        
        low_stock_count = Product.objects.filter(stock_quantity__lte=10, is_active=True).count()
        total_products = Product.objects.filter(is_active=True).count()
        
        week_ago = today - timedelta(days=7)
        revenue_week = Sale.objects.filter(created_at__date__gte=week_ago, status='completed').aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        
        top_products = SaleItem.objects.all().values(
            'product__id', 'product__name'
        ).annotate(
            total_sold=Sum('quantity'),
            total_revenue=Sum('total_price')
        ).order_by('-total_sold')[:5]
        
        return Response({
            'total_sales_today': total_sales_today,
            'revenue_today': revenue_today,
            'revenue_week': revenue_week,
            'low_stock_count': low_stock_count,
            'total_products': total_products,
            'top_products': list(top_products)
        })


urlpatterns = [
    path('', api_root, name='api-root'),
    path('dashboard/', DashboardAPI.as_view(), name='dashboard'),
    path('dashboard/stats/', DashboardAPI.as_view(), name='dashboard-stats'),
]