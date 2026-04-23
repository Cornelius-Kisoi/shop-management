from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import CreditCategory, Credit
from sales.models import Sale, SaleItem
from products.models import Product
from .serializers import CreditCategorySerializer, CreditSerializer


class CreditCategoryViewSet(viewsets.ModelViewSet):
    queryset = CreditCategory.objects.all()
    serializer_class = CreditCategorySerializer
    permission_classes = [IsAuthenticated]


class CreditViewSet(viewsets.ModelViewSet):
    queryset = Credit.objects.all()
    serializer_class = CreditSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        credits = Credit.objects.all()
        if start_date:
            credits = credits.filter(date__gte=start_date)
        if end_date:
            credits = credits.filter(date__lte=end_date)
        
        total = credits.aggregate(total=Sum('amount'))['total'] or 0
        by_category = credits.values('category__name').annotate(total=Sum('amount'))
        
        return Response({
            'total': total,
            'by_category': list(by_category)
        })


class ReportViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        today = timezone.now().date()
        
        total_sales_today = Sale.objects.filter(created_at__date=today, status='completed').count()
        revenue_today = Sale.objects.filter(created_at__date=today, status='completed').aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        
        low_stock_count = Product.objects.filter(stock_quantity__lte=10, is_active=True).count()
        
        total_products = Product.objects.filter(is_active=True).count()
        
        return Response({
            'total_sales_today': total_sales_today,
            'revenue_today': revenue_today,
            'low_stock_count': low_stock_count,
            'total_products': total_products
        })
    
    @action(detail=False, methods=['get'])
    def sales_report(self, request):
        period = request.query_params.get('period', 'week')
        now = timezone.now()
        
        if period == 'day':
            start = now.replace(hour=0, minute=0, second=0)
        elif period == 'week':
            start = now - timedelta(days=7)
        elif period == 'month':
            start = now - timedelta(days=30)
        else:
            start = now - timedelta(days=30)
        
        sales = Sale.objects.filter(created_at__gte=start, status='completed')
        total_revenue = sales.aggregate(total=Sum('total_amount'))['total'] or 0
        total_count = sales.count()
        
        daily_sales = sales.extra(select={'day': "date(created_at)"}).values('day').annotate(
            total=Sum('total_amount'), count=Count('id')
        )
        
        return Response({
            'period': period,
            'total_revenue': total_revenue,
            'total_count': total_count,
            'daily_sales': list(daily_sales)
        })
    
    @action(detail=False, methods=['get'])
    def top_products(self, request):
        limit = int(request.query_params.get('limit', 10))
        items = SaleItem.objects.all().values(
            'product__id', 'product__name'
        ).annotate(
            total_sold=Sum('quantity'),
            total_revenue=Sum('total_price')
        ).order_by('-total_sold')[:limit]
        
        return Response(list(items))