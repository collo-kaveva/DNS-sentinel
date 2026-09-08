"""
Views for the lifecycle app.
"""
from django.db import models
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Evidence, EvidenceRelationship, LifecycleAssessment
from .serializers import EvidenceSerializer, EvidenceRelationshipSerializer, LifecycleAssessmentSerializer
from .classification_engine import LifecycleClassificationEngine


class EvidenceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Evidence model.
    
    Provides CRUD operations for evidence items with filtering by:
    - Asset/domain
    - Evidence type
    - Source
    - Date range
    - Confidence
    - Observation category
    """
    serializer_class = EvidenceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["observation", "entity_name", "source"]
    ordering_fields = ["observed_at", "confidence", "evidence_type"]
    ordering = ["-observed_at"]
    
    def get_queryset(self):
        """Filter evidence by current user."""
        queryset = Evidence.objects.filter(owner=self.request.user)
        
        # Filter by domain if provided
        domain_id = self.request.query_params.get("domain")
        if domain_id:
            queryset = queryset.filter(domain_id=domain_id)
        
        # Filter by evidence type if provided
        evidence_type = self.request.query_params.get("evidence_type")
        if evidence_type:
            queryset = queryset.filter(evidence_type=evidence_type)
        
        # Filter by status if provided
        status = self.request.query_params.get("status")
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by source if provided
        source = self.request.query_params.get("source")
        if source:
            queryset = queryset.filter(source=source)
        
        # Filter by confidence if provided
        confidence = self.request.query_params.get("confidence")
        if confidence:
            queryset = queryset.filter(confidence=confidence)
        
        # Filter by date range if provided
        date_from = self.request.query_params.get("date_from")
        date_to = self.request.query_params.get("date_to")
        if date_from:
            queryset = queryset.filter(observed_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(observed_at__lte=date_to)
        
        return queryset
    
    def perform_create(self, serializer):
        """Set the owner to the current user."""
        serializer.save(owner=self.request.user)
    
    @action(detail=False, methods=["get"])
    def for_asset(self, request):
        """Get all evidence for a specific asset/domain."""
        domain_id = request.query_params.get("domain_id")
        if not domain_id:
            return Response({"detail": "domain_id parameter is required"}, status=400)
        
        evidence = self.get_queryset().filter(domain_id=domain_id)
        page = self.paginate_queryset(evidence)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(evidence, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=["get"])
    def related(self, request):
        """Get evidence related to a specific evidence item."""
        evidence_id = request.query_params.get("evidence_id")
        if not evidence_id:
            return Response({"detail": "evidence_id parameter is required"}, status=400)
        
        try:
            evidence = Evidence.objects.get(id=evidence_id, owner=request.user)
        except Evidence.DoesNotExist:
            return Response({"detail": "Evidence not found"}, status=404)
        
        # Get evidence relationships
        relationships_from = EvidenceRelationship.objects.filter(from_evidence=evidence)
        relationships_to = EvidenceRelationship.objects.filter(to_evidence=evidence)
        
        # Get related evidence IDs
        related_ids = set()
        for rel in relationships_from:
            related_ids.add(rel.to_evidence.id)
        for rel in relationships_to:
            related_ids.add(rel.from_evidence.id)
        
        # Get related evidence
        related_evidence = Evidence.objects.filter(
            id__in=related_ids,
            owner=request.user
        )
        
        serializer = EvidenceSerializer(related_evidence, many=True)
        return Response(serializer.data)


class EvidenceRelationshipViewSet(viewsets.ModelViewSet):
    """
    ViewSet for EvidenceRelationship model.
    
    Provides CRUD operations for evidence relationships.
    """
    serializer_class = EvidenceRelationshipSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["relationship_type"]
    ordering_fields = ["observed_at", "confidence"]
    ordering = ["-observed_at"]
    
    def get_queryset(self):
        """Filter relationships by current user's evidence."""
        queryset = EvidenceRelationship.objects.filter(
            from_evidence__owner=self.request.user
        )
        
        # Filter by evidence if provided
        evidence_id = self.request.query_params.get("evidence_id")
        if evidence_id:
            queryset = queryset.filter(
                models.Q(from_evidence_id=evidence_id) | models.Q(to_evidence_id=evidence_id)
            )
        
        # Filter by relationship type if provided
        relationship_type = self.request.query_params.get("relationship_type")
        if relationship_type:
            queryset = queryset.filter(relationship_type=relationship_type)
        
        return queryset


class LifecycleAssessmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for LifecycleAssessment model.
    
    Provides CRUD operations for lifecycle assessments.
    """
    serializer_class = LifecycleAssessmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["explanation", "limitations"]
    ordering_fields = ["generated_at", "confidence", "classification"]
    ordering = ["-generated_at"]
    
    def get_queryset(self):
        """Filter assessments by current user."""
        queryset = LifecycleAssessment.objects.filter(owner=self.request.user)
        
        # Filter by domain if provided
        domain_id = self.request.query_params.get("domain")
        if domain_id:
            queryset = queryset.filter(domain_id=domain_id)
        
        # Filter by classification if provided
        classification = self.request.query_params.get("classification")
        if classification:
            queryset = queryset.filter(classification=classification)
        
        return queryset
    
    def perform_create(self, serializer):
        """Set the owner to the current user."""
        serializer.save(owner=self.request.user)
    
    @action(detail=False, methods=["get"])
    def latest(self, request):
        """Get the latest lifecycle assessment for a domain."""
        domain_id = request.query_params.get("domain_id")
        if not domain_id:
            return Response({"detail": "domain_id parameter is required"}, status=400)
        
        try:
            assessment = LifecycleAssessment.objects.filter(
                domain_id=domain_id,
                owner=request.user
            ).first()
            
            if not assessment:
                return Response({"detail": "No assessment found for this domain"}, status=404)
            
            serializer = self.get_serializer(assessment)
            return Response(serializer.data)
        except Exception as e:
            return Response({"detail": str(e)}, status=400)
    
    @action(detail=False, methods=["post"])
    def classify(self, request):
        """Trigger lifecycle classification for a domain."""
        domain_id = request.data.get("domain_id")
        if not domain_id:
            return Response({"detail": "domain_id parameter is required"}, status=400)
        
        # Verify user owns the domain
        from apps.dns_intelligence.models import Domain
        try:
            domain = Domain.objects.get(id=domain_id, owner=request.user)
        except Domain.DoesNotExist:
            return Response({"detail": "Domain not found"}, status=404)
        
        # Run classification
        try:
            classification_result = LifecycleClassificationEngine.classify_domain(domain)
            assessment = LifecycleClassificationEngine.save_lifecycle_assessment(domain, classification_result)
            
            serializer = self.get_serializer(assessment)
            return Response(serializer.data, status=201)
        except Exception as e:
            return Response({"detail": f"Classification failed: {str(e)}"}, status=400)
