"""
Views for the monitoring app.
"""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import MonitoringConfig, MonitoringResult, ChangeEvent
from .serializers import MonitoringConfigSerializer, MonitoringResultSerializer, ChangeEventSerializer


class MonitoringConfigViewSet(viewsets.ModelViewSet):
    """
    Monitoring configurations for domains.
    
    /api/monitoring/configs/              list / create
    /api/monitoring/configs/{id}/         retrieve / update / delete
    /api/monitoring/configs/{id}/results/  monitoring results for this config
    """
    serializer_class = MonitoringConfigSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["monitor_type", "is_enabled", "frequency"]
    search_fields = ["domain__name", "notes"]
    ordering_fields = ["created_at", "updated_at", "next_check_scheduled"]
    
    def get_queryset(self):
        return MonitoringConfig.objects.filter(owner=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
    
    @action(detail=True, methods=["get"])
    def results(self, request, pk=None):
        """Get monitoring results for this configuration."""
        config = self.get_object()
        qs = MonitoringResult.objects.filter(monitoring_config=config)
        return Response(MonitoringResultSerializer(qs, many=True).data)


class MonitoringResultViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Monitoring results from periodic checks.
    
    /api/monitoring/results/               list
    /api/monitoring/results/{id}/          retrieve
    /api/monitoring/results/{id}/changes/  change events for this result
    """
    serializer_class = MonitoringResultSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["monitor_type", "status", "has_changes"]
    ordering_fields = ["created_at", "check_started_at", "check_completed_at"]
    
    def get_queryset(self):
        return MonitoringResult.objects.filter(
            monitoring_config__owner=self.request.user
        ).select_related("domain", "monitoring_config")
    
    @action(detail=True, methods=["get"])
    def changes(self, request, pk=None):
        """Get change events for this monitoring result."""
        result = self.get_object()
        qs = ChangeEvent.objects.filter(monitoring_result=result)
        return Response(ChangeEventSerializer(qs, many=True).data)


class ChangeEventViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Change events detected during monitoring.
    
    /api/monitoring/changes/               list
    /api/monitoring/changes/{id}/          retrieve
    """
    serializer_class = ChangeEventSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["event_type", "alert_generated"]
    search_fields = ["domain__name", "entity_name", "description"]
    ordering_fields = ["detected_at"]
    
    def get_queryset(self):
        return ChangeEvent.objects.filter(
            monitoring_result__monitoring_config__owner=self.request.user
        ).select_related("domain", "monitoring_result")