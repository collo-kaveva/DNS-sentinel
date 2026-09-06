"""
Views for the investigation app.
"""
from django.utils import timezone
from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Investigation, AnalystNote
from .serializers import InvestigationSerializer, AnalystNoteSerializer


class InvestigationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Investigation model.
    
    Provides CRUD operations for investigations with filtering capabilities.
    """
    serializer_class = InvestigationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title", "description", "domain__name"]
    ordering_fields = ["created_at", "updated_at", "status", "priority"]
    ordering = ["-created_at"]
    
    def get_queryset(self):
        """Filter investigations by current user."""
        queryset = Investigation.objects.filter(owner=self.request.user)
        
        # Filter by domain if provided
        domain_id = self.request.query_params.get("domain")
        if domain_id:
            queryset = queryset.filter(domain_id=domain_id)
        
        # Filter by status if provided
        status = self.request.query_params.get("status")
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by priority if provided
        priority = self.request.query_params.get("priority")
        if priority:
            queryset = queryset.filter(priority=priority)
        
        # Filter by assigned analyst if provided
        assigned_analyst = self.request.query_params.get("assigned_analyst")
        if assigned_analyst:
            queryset = queryset.filter(assigned_analyst_id=assigned_analyst)
        
        return queryset
    
    def perform_create(self, serializer):
        """Set the owner to the current user."""
        serializer.save(owner=self.request.user)
    
    @action(detail=True, methods=["post"])
    def change_status(self, request, pk=None):
        """Change the status of an investigation."""
        investigation = self.get_object()
        new_status = request.data.get("status")
        
        if not new_status:
            return Response({"detail": "status field is required"}, status=400)
        
        if new_status not in Investigation.Status.values:
            return Response({"detail": "Invalid status value"}, status=400)
        
        investigation.status = new_status
        
        # Set closed_at timestamp when closing
        if new_status == Investigation.Status.CLOSED:
            investigation.closed_at = timezone.now()
        elif investigation.closed_at and new_status != Investigation.Status.CLOSED:
            investigation.closed_at = None
        
        investigation.save()
        serializer = self.get_serializer(investigation)
        return Response(serializer.data)
    
    @action(detail=True, methods=["post"])
    def assign(self, request, pk=None):
        """Assign an analyst to an investigation."""
        investigation = self.get_object()
        analyst_id = request.data.get("analyst_id")
        
        if not analyst_id:
            return Response({"detail": "analyst_id field is required"}, status=400)
        
        investigation.assigned_analyst_id = analyst_id
        investigation.save()
        serializer = self.get_serializer(investigation)
        return Response(serializer.data)
    
    @action(detail=True, methods=["get"])
    def timeline(self, request, pk=None):
        """Get the timeline for an investigation."""
        from apps.lifecycle.timeline_service import TimelineService
        
        investigation = self.get_object()
        
        # Get timeline events using the timeline service
        limit = request.query_params.get("limit", 100)
        try:
            limit = int(limit)
        except ValueError:
            limit = 100
        
        timeline = TimelineService.get_investigation_timeline(
            investigation_id=str(investigation.id),
            user_id=request.user.id,
            limit=limit
        )
        
        return Response({
            "investigation_id": str(investigation.id),
            "timeline": timeline,
        })
    
    @action(detail=True, methods=["get"])
    def related_evidence(self, request, pk=None):
        """Get evidence related to this investigation."""
        investigation = self.get_object()
        
        # Return the related evidence IDs
        return Response({
            "investigation_id": str(investigation.id),
            "related_evidence": investigation.related_evidence,
        })
    
    @action(detail=True, methods=["post"])
    def add_evidence(self, request, pk=None):
        """Add evidence to an investigation."""
        investigation = self.get_object()
        evidence_id = request.data.get("evidence_id")
        
        if not evidence_id:
            return Response({"detail": "evidence_id field is required"}, status=400)
        
        if evidence_id not in investigation.related_evidence:
            investigation.related_evidence.append(evidence_id)
            investigation.save()
        
        return Response({"related_evidence": investigation.related_evidence})


class AnalystNoteViewSet(viewsets.ModelViewSet):
    """
    ViewSet for AnalystNote model.
    
    Provides CRUD operations for analyst notes with authorization checks.
    """
    serializer_class = AnalystNoteSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["content"]
    ordering_fields = ["created_at", "updated_at"]
    ordering = ["-created_at"]
    
    def get_queryset(self):
        """Filter notes by current user and investigation."""
        queryset = AnalystNote.objects.filter(author=self.request.user)
        
        # Filter by investigation if provided
        investigation_id = self.request.query_params.get("investigation")
        if investigation_id:
            queryset = queryset.filter(investigation_id=investigation_id)
        
        return queryset
    
    def perform_create(self, serializer):
        """Set the author to the current user."""
        serializer.save(author=self.request.user)
    
    def perform_update(self, serializer):
        """Only allow the author to update their own notes."""
        if self.get_object().author != self.request.user:
            return Response({"detail": "You can only update your own notes"}, status=403)
        serializer.save()
    
    def perform_destroy(self, instance):
        """Only allow the author to delete their own notes."""
        if instance.author != self.request.user:
            return Response({"detail": "You can only delete your own notes"}, status=403)
        instance.delete()
