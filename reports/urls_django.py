from django.urls import path
from . import views_django as views

app_name = 'reports'

urlpatterns = [
    path('', views.expense_list, name='expense_list'),
    path('add/', views.expense_create, name='expense_create'),
    path('categories/', views.expense_category_list, name='category_list'),
    path('categories/add/', views.expense_category_create, name='category_create'),
    path('summary/', views.summary, name='summary'),
    path('debts/', views.customer_debts, name='customer_debts'),
    path('debts/record-payment/', views.record_customer_payment, name='record_payment'),
    path('debts/receipt/', views.debts_receipt, name='debts_receipt'),
    path('credit/<int:pk>/receipt/', views.credit_receipt, name='credit_receipt'),
]