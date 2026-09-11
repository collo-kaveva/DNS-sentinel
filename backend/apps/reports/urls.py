"""
URL configuration for the reports app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ReportViewSet, ReportSectionViewSet

router = DefaultRouter()
router.register(r"", ReportViewSet, basename="report")
router.register(r"sections", ReportSectionViewSet, basename="report-section")

urlpatterns = [
    path("", include(router.urls)),
]