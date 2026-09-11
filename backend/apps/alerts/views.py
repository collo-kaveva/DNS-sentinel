"""
Views for the alerts app.
"""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Alert, AlertRule
from .serializers import (
    AlertSerializer, AlertCreateSerializer, AlertStatusTransitionSerializer,
    AlertAssignmentSerializer, AlertInvestigationSerializer, AlertRuleSerializer
)


class AlertViewSet(viewsets.ModelViewSet):
    """
    Alert management endpoints.
    
    /api/alerts/                           list / create
    /api/alerts/{id}/                      retrieve / update / delete
    /api/alerts/{id}/acknowledge/          acknowledge alert
    /api/alerts/{id}/resolve/               resolve alert
    /api/alerts/{id}/reopen/               reopen alert
    /api/alerts/{id}/dismiss/              dismiss alert
    /api/alerts/{id}/assign/               assign to analyst
    /api/alerts/{id}/investigation/        link to investigation
    /api/alerts/{id}/evidence/             related evidence
    """
    serializer_class = AlertSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["alert_type", "severity", "status", "domain"]
    search_fields = ["title", "description", "domain__name"]
    ordering_fields = ["created_at", "severity", "status"]
    
    def get_queryset(self):
        return Alert.objects.filter(owner=self.request.user).select_related(
            "domain", "owner", "assigned_analyst", "investigation"
        )
    
    def get_serializer_class(self):
        if self.action == "create":
            return AlertCreateSerializer
        return AlertSerializer
    
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
    
    @action(detail=True, methods=["post"])
    def acknowledge(self, request, pk=None):
        """Acknowledge an alert."""
        alert = self.get_object()
        serializer = AlertStatusTransitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        new_status = serializer.validated_data["status"]
        notes = serializer.validated_data.get("notes", "")
        
        if new_status != Alert.Status.ACKNOWLEDGED:
            return Response(
                {"detail": "Invalid status for acknowledge action"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if alert.transition_to(new_status, user=request.user, notes=notes):
            return Response(AlertSerializer(alert).data)
        return Response(
            {"detail": "Invalid state transition"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=["post"])
    def resolve(self, request, pk=None):
        """Resolve an alert."""
        alert = self.get_object()
        serializer = AlertStatusTransitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        new_status = serializer.validated_data["status"]
        notes = serializer.validated_data.get("notes", "")
        
        if new_status != Alert.Status.RESOLVED:
            return Response(
                {"detail": "Invalid status for resolve action"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if alert.transition_to(new_status, user=request.user, notes=notes):
            return Response(AlertSerializer(alert).data)
        return Response(
            {"detail": "Invalid state transition"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=["post"])
    def reopen(self, request, pk=None):
        """Reopen a resolved alert."""
        alert = self.get_object()
        
        if alert.transition_to(Alert.Status.OPEN, user=request.user):
            return Response(AlertSerializer(alert).data)
        return Response(
            {"detail": "Cannot reopen this alert"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=["post"])
    def dismiss(self, request, pk=None):
        """Dismiss an alert."""
        alert = self.get_object()
        serializer = AlertStatusTransitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        new_status = serializer.validated_data["status"]
        notes = serializer.validated_data.get("notes", "")
        
        if new_status != Alert.Status.DISMISSED:
            return Response(
                {"detail": "Invalid status for dismiss action"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if alert.transition_to(new_status, user=request.user, notes=notes):
            return Response(AlertSerializer(alert).data)
        return Response(
            {"detail": "Invalid state transition"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=["post"])
    def assign(self, request, pk=None):
        """Assign an alert to an analyst."""
        alert = self.get_object()
        serializer = AlertAssignmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        analyst_id = serializer.validated_data.get("assigned_analyst_id")
        
        # Only allow assigning to users in the same organization or self
        # For now, allow any user assignment
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        if analyst_id:
            try:
                analyst = User.objects.get(id=analyst_id)
                alert.assigned_analyst = analyst
            except User.DoesNotExist:
                return Response(
                    {"detail": "Analyst not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            alert.assigned_analyst = None
        
        alert.save()
        
        # Create audit event
        from apps.accounts.services import AuditService
        AuditService.log_alert_assigned(request.user, alert, analyst_id)
        
        return Response(AlertSerializer(alert).data)
    
    @action(detail=True, methods=["post"])
    def investigation(self, request, pk=None):
        """Link an alert to an investigation."""
        alert = self.get_object()
        serializer = AlertInvestigationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        investigation_id = serializer.validated_data.get("investigation_id")
        
        if investigation_id:
            from apps.investigation.models import Investigation
            try:
                investigation = Investigation.objects.get(id=investigation_id, owner=request.user)
                alert.investigation = investigation
            except Investigation.DoesNotExist:
                return Response(
                    {"detail": "Investigation not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            alert.investigation = None
        
        alert.save()
        return Response(AlertSerializer(alert).data)
    
    @action(detail=True, methods=["get"])
    def evidence(self, request, pk=None):
        """Get evidence related to this alert."""
        alert = self.get_object()
        
        if not alert.evidence_id:
            return Response({"evidence": None})
        
        from apps.lifecycle.models import Evidence
        try:
            evidence = Evidence.objects.get(id=alert.evidence_id)
            from apps.lifecycle.serializers import EvidenceSerializer
            return Response({"evidence": EvidenceSerializer(evidence).data})
        except Evidence.DoesNotExist:
            return Response({"evidence": None}, status=status.HTTP_404_NOT_FOUND)


class AlertRuleViewSet(viewsets.ModelViewSet):
    """
    Alert rule management endpoints.
    
    /api/alerts/rules/                     list / create
    /api/alerts/rules/{id}/                retrieve / update / delete
    """
    serializer_class = AlertRuleSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["alert_type", "severity", "enabled"]
    search_fields = ["name", "description"]
    ordering_fields = ["created_at", "name"]
    
    def get_queryset(self):
        return AlertRule.objects.filter(owner=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)