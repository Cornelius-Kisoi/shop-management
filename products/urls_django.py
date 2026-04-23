from django.urls import path
from . import views_django as views

app_name = 'products'

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('add/', views.product_create, name='product_create'),
    path('bulk-upload/', views.product_bulk_upload, name='product_bulk_upload'),
    path('bulk-upload/template/', views.download_product_upload_template, name='product_bulk_upload_template'),
    path('<int:pk>/edit/', views.product_edit, name='product_edit'),
    path('<int:pk>/delete/', views.product_delete, name='product_delete'),
    path('stock-history/', views.stock_history, name='stock_history'),
    path('categories/', views.category_list, name='category_list'),
    path('categories/add/', views.category_create, name='category_create'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/add/', views.supplier_create, name='supplier_create'),
    path('suppliers/<int:pk>/delete/', views.supplier_delete, name='supplier_delete'),
]