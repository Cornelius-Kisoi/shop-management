from django.contrib import admin
from .models import CreditCategory, Credit


@admin.register(CreditCategory)
class CreditCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']


@admin.register(Credit)
class CreditAdmin(admin.ModelAdmin):
    list_display = ['date', 'customer', 'amount', 'amount_paid', 'outstanding_balance', 'status', 'created_by']
    list_filter = ['category', 'status', 'date']
    search_fields = ['description', 'customer__name']
    readonly_fields = ['created_at', 'outstanding_balance']