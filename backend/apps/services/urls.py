"""
URL configuration for the services app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ServiceViewSet, ServiceObservationViewSet

router = DefaultRouter()
router.register(r"services", ServiceViewSet, basename="service")
router.register(r"service-observations", ServiceObservationViewSet, basename="service-observation")

urlpatterns = [
    path("", include(router.urls)),
]
