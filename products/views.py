from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Supplier, Category, Product, StockHistory
from .serializers import (
    SupplierSerializer, CategorySerializer, ProductSerializer,
    ProductCreateSerializer, StockHistorySerializer
)


class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'email', 'phone']
    ordering_fields = ['name', 'created_at']


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields = ['category', 'supplier', 'is_active', 'is_low_stock']
    search_fields = ['name', 'sku', 'barcode']
    ordering_fields = ['name', 'selling_price', 'stock_quantity', 'created_at']
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ProductCreateSerializer
        return ProductSerializer
    
    def perform_create(self, serializer):
        product = serializer.save()
        StockHistory.objects.create(
            product=product,
            action='adjustment',
            quantity=product.stock_quantity,
            reference='Initial Stock',
            created_by=self.request.user
        )
    
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        products = Product.objects.filter(stock_quantity__lte=10, is_active=True)
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)


class StockHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StockHistory.objects.all()
    serializer_class = StockHistorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields = ['product', 'action']
    search_fields = ['product__name', 'reference']
    ordering_fields = ['created_at']