from django.urls import path
from . import views_django as views

app_name = 'users'

urlpatterns = [
    path('', views.user_list, name='user_list'),
    path('add/', views.user_create, name='user_create'),
    path('<int:pk>/edit/', views.user_edit, name='user_edit'),
    path('<int:pk>/delete/', views.user_delete, name='user_delete'),
    path('<int:pk>/archive/', views.user_toggle_archive, name='user_toggle_archive'),
]