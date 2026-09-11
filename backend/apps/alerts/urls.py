"""
URL configuration for the alerts app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import AlertViewSet, AlertRuleViewSet

router = DefaultRouter()
router.register(r"", AlertViewSet, basename="alert")
router.register(r"rules", AlertRuleViewSet, basename="alert-rule")

urlpatterns = [
    path("", include(router.urls)),
]