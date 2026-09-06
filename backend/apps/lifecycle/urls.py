"""
URL configuration for the lifecycle app.
"""
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r"evidence", views.EvidenceViewSet, basename="evidence")
router.register(r"evidence-relationships", views.EvidenceRelationshipViewSet, basename="evidence-relationship")
router.register(r"lifecycle-assessments", views.LifecycleAssessmentViewSet, basename="lifecycle-assessment")

urlpatterns = router.urls
