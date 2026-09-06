"""
URL configuration for the investigation app.
"""
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r"investigations", views.InvestigationViewSet, basename="investigation")
router.register(r"analyst-notes", views.AnalystNoteViewSet, basename="analyst-note")

urlpatterns = router.urls
