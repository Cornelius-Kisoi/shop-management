from rest_framework import serializers
from .models import Supplier, Category, Product, StockHistory


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = '__all__'


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'sku', 'barcode', 'category', 'category_name', 'supplier', 'supplier_name', 
                 'description', 'cost_price', 'selling_price', 'stock_quantity', 'low_stock_threshold',
                 'is_active', 'is_low_stock', 'created_at', 'updated_at']


class ProductCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['name', 'sku', 'barcode', 'category', 'supplier', 'description', 'cost_price', 
                  'selling_price', 'stock_quantity', 'low_stock_threshold', 'is_active']


class StockHistorySerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = StockHistory
        fields = '__all__'