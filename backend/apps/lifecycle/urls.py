"""
URL configuration for the lifecycle app.
"""
from rest_framework.routers import DefaultRouter
from django.urls import path
from . import views
from .history_api import UnifiedHistoryViewSet

router = DefaultRouter()
router.register(r"evidence", views.EvidenceViewSet, basename="evidence")
router.register(r"evidence-relationships", views.EvidenceRelationshipViewSet, basename="evidence-relationship")
router.register(r"lifecycle-assessments", views.LifecycleAssessmentViewSet, basename="lifecycle-assessment")

# History API endpoints
history_viewset = UnifiedHistoryViewSet.as_view({
    "get": "list",
})
history_timeline = UnifiedHistoryViewSet.as_view({
    "get": "timeline",
})
history_asset = UnifiedHistoryViewSet.as_view({
    "get": "asset_history",
})

urlpatterns = router.urls + [
    path("history/", history_viewset, name="history-list"),
    path("history/timeline/", history_timeline, name="history-timeline"),
    path("history/asset/", history_asset, name="history-asset"),
]
