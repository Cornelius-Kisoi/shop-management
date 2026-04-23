from django.contrib.admin import AdminSite


class CkayStoresAdminSite(AdminSite):
    site_header = 'EXTREME TECH Admin'
    site_title = 'EXTREME TECH'
    index_title = 'Dashboard'
    
    def index(self, request, extra_context=None):
        from django.db.models import Sum
        from django.utils import timezone
        from datetime import timedelta
        from sales.models import Sale
        from products.models import Product
        from customers.models import Customer
        
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        
        sales_today = Sale.objects.filter(created_at__date=today, status='completed').count()
        revenue_today = Sale.objects.filter(created_at__date=today, status='completed').aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        
        revenue_week = Sale.objects.filter(created_at__date__gte=week_ago, status='completed').aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        
        low_stock = Product.objects.filter(stock_quantity__lte=10, is_active=True).count()
        total_products = Product.objects.filter(is_active=True).count()
        total_customers = Customer.objects.count()
        
        extra_context = extra_context or {}
        extra_context.update({
            'sales_today': sales_today,
            'revenue_today': revenue_today,
            'revenue_week': revenue_week,
            'low_stock': low_stock,
            'total_products': total_products,
            'total_customers': total_customers,
        })
        return super().index(request, extra_context)


site = CkayStoresAdminSite()