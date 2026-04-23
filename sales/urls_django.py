from django.urls import path
from . import views_django as views

app_name = 'sales'

urlpatterns = [
    path('', views.sale_list, name='sale_list'),
    path('pos/', views.pos, name='pos'),
    path('pos/search/', views.pos_search_products, name='pos_search'),
    path('pos/process/', views.pos_process_sale, name='pos_process'),
    path('receipt/<int:pk>/', views.sale_receipt, name='receipt'),
    path('receipts/', views.receipt_list, name='receipts'),
    path('receipt/<int:pk>/send/', views.send_receipt, name='send_receipt'),
    path('reset-data/', views.reset_sales_and_credits, name='reset_data'),
    path('new/', views.sale_create, name='sale_create'),
    path('<int:pk>/', views.sale_detail, name='sale_detail'),
]