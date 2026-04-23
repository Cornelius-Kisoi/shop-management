from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SupplierViewSet, CategoryViewSet, ProductViewSet, StockHistoryViewSet

router = DefaultRouter()
router.register(r'suppliers', SupplierViewSet, basename='suppliers')
router.register(r'categories', CategoryViewSet, basename='categories')
router.register(r'products', ProductViewSet, basename='products')
router.register(r'stock-history', StockHistoryViewSet, basename='stock-history')

urlpatterns = [
    path('', include(router.urls)),
]