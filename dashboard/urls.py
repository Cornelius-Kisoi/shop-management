from django.urls import path
from . import views_django as views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
]