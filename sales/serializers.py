from rest_framework import serializers
from .models import Sale, SaleItem
from customers.models import Customer


class SaleItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = SaleItem
        fields = ['id', 'product', 'product_name', 'quantity', 'unit_price', 'total_price']


class SaleSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    items = SaleItemSerializer(many=True, read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Sale
        fields = ['id', 'invoice_number', 'customer', 'customer_name', 'subtotal', 'tax_amount', 
                  'discount_amount', 'total_amount', 'amount_paid', 'change_given', 'status',
                  'notes', 'created_by', 'created_by_username', 'items', 'created_at', 'updated_at']
        read_only_fields = ['invoice_number', 'subtotal', 'total_amount', 'created_at']


class SaleCreateSerializer(serializers.Serializer):
    customer = serializers.PrimaryKeyRelatedField(queryset=Customer.objects.all(), required=False, allow_null=True)
    items = serializers.ListField(
        child=serializers.DictField(
            child=serializers.IntegerField()
        )
    )
    amount_paid = serializers.DecimalField(max_digits=12, decimal_places=2)
    discount_amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, default=0)
    notes = serializers.CharField(required=False, allow_blank=True)