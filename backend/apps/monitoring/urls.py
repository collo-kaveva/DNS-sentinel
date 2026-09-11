"""
URL configuration for the monitoring app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import MonitoringConfigViewSet, MonitoringResultViewSet, ChangeEventViewSet

router = DefaultRouter()
router.register(r"configs", MonitoringConfigViewSet, basename="monitoring-config")
router.register(r"results", MonitoringResultViewSet, basename="monitoring-result")
router.register(r"changes", ChangeEventViewSet, basename="change-event")

urlpatterns = [
    path("", include(router.urls)),
]