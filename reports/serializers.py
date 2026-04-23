from rest_framework import serializers
from .models import CreditCategory, Credit


class CreditCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditCategory
        fields = '__all__'


class CreditSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    outstanding_balance = serializers.ReadOnlyField()
    
    class Meta:
        model = Credit
        fields = ['id', 'category', 'category_name', 'customer', 'amount', 'amount_paid', 
                'outstanding_balance', 'description', 'date', 'due_date', 'status',
                'created_by', 'created_by_username', 'created_at']
        read_only_fields = ['created_at']