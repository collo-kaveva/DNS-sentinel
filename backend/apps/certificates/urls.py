"""
URL configuration for the certificates app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import CertificateViewSet, CertificateObservationViewSet

router = DefaultRouter()
router.register(r"certificates", CertificateViewSet, basename="certificate")
router.register(r"certificate-observations", CertificateObservationViewSet, basename="certificate-observation")

urlpatterns = [
    path("", include(router.urls)),
]
