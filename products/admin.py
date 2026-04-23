from django.contrib import admin
from .models import Supplier, Category, Product, StockHistory


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_person', 'email', 'phone']
    search_fields = ['name', 'email', 'phone']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'sku', 'category', 'selling_price', 'stock_quantity', 'is_active', 'is_low_stock']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'sku', 'barcode']
    list_editable = ['is_active', 'stock_quantity']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(StockHistory)
class StockHistoryAdmin(admin.ModelAdmin):
    list_display = ['product', 'action', 'quantity', 'reference', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['product__name', 'reference']
    readonly_fields = ['created_at']