from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CreditCategoryViewSet, CreditViewSet, ReportViewSet

router = DefaultRouter()
router.register(r'categories', CreditCategoryViewSet, basename='credit-categories')
router.register(r'credits', CreditViewSet, basename='credits')
router.register(r'reports', ReportViewSet, basename='reports')

urlpatterns = [
    path('', include(router.urls)),
]