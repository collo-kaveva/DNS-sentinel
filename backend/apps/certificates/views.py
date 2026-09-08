"""
Views for the certificates app.
"""
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Certificate, CertificateObservation
from .serializers import (
    CertificateSerializer,
    CertificateObservationSerializer,
    CertificateStatusSerializer,
    IssuerDistributionSerializer,
    CertificateChangeSerializer,
)


class CertificateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Certificate model.
    
    Provides CRUD operations for certificates with filtering by:
    - Asset/domain
    - Issuer
    - Validity status
    - Expiration date range
    - Date observed
    """
    serializer_class = CertificateSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["subject", "issuer", "sans"]
    ordering_fields = ["valid_until", "collection_timestamp", "last_seen"]
    ordering = ["-last_seen"]
    
    def get_queryset(self):
        """Filter certificates by current user."""
        queryset = Certificate.objects.filter(domain__owner=self.request.user)
        
        # Filter by domain if provided
        domain_id = self.request.query_params.get("domain")
        if domain_id:
            queryset = queryset.filter(domain_id=domain_id)
        
        # Filter by issuer if provided
        issuer = self.request.query_params.get("issuer")
        if issuer:
            queryset = queryset.filter(issuer__icontains=issuer)
        
        # Filter by validity status
        is_valid = self.request.query_params.get("is_valid")
        if is_valid is not None:
            queryset = queryset.filter(is_valid=is_valid.lower() == "true")
        
        # Filter by expiration status
        is_expired = self.request.query_params.get("is_expired")
        if is_expired is not None:
            queryset = queryset.filter(is_expired=is_expired.lower() == "true")
        
        # Filter by expiration date range
        expiring_before = self.request.query_params.get("expiring_before")
        expiring_after = self.request.query_params.get("expiring_after")
        if expiring_before:
            queryset = queryset.filter(valid_until__lte=expiring_before)
        if expiring_after:
            queryset = queryset.filter(valid_until__gte=expiring_after)
        
        # Filter by date range
        date_from = self.request.query_params.get("date_from")
        date_to = self.request.query_params.get("date_to")
        if date_from:
            queryset = queryset.filter(collection_timestamp__gte=date_from)
        if date_to:
            queryset = queryset.filter(collection_timestamp__lte=date_to)
        
        return queryset
    
    @action(detail=False, methods=["get"])
    def history(self, request):
        """Get certificate history for a domain."""
        domain_id = request.query_params.get("domain_id")
        if not domain_id:
            return Response({"detail": "domain_id parameter is required"}, status=400)
        
        # Verify user owns the domain
        from apps.dns_intelligence.models import Domain
        try:
            domain = Domain.objects.get(id=domain_id, owner=request.user)
        except Domain.DoesNotExist:
            return Response({"detail": "Domain not found"}, status=404)
        
        # Get certificate observations
        observations = CertificateObservation.objects.filter(
            domain=domain
        ).order_by("-observed_at")
        
        page = self.paginate_queryset(observations)
        if page is not None:
            serializer = CertificateObservationSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = CertificateObservationSerializer(observations, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=["get"])
    def status(self, request):
        """Get certificate status for a domain."""
        domain_id = request.query_params.get("domain_id")
        if not domain_id:
            return Response({"detail": "domain_id parameter is required"}, status=400)
        
        # Verify user owns the domain
        from apps.dns_intelligence.models import Domain
        try:
            domain = Domain.objects.get(id=domain_id, owner=request.user)
        except Domain.DoesNotExist:
            return Response({"detail": "Domain not found"}, status=404)
        
        # Get current certificate
        certificate = Certificate.objects.filter(domain=domain).first()
        
        if not certificate:
            return Response({
                "domain_id": str(domain.id),
                "domain_name": domain.name,
                "has_certificate": False,
                "is_valid": False,
                "is_expired": False,
                "days_until_expiry": None,
                "issuer": None,
                "subject": None,
                "last_observed": None,
            })
        
        # Calculate days until expiry
        days_until_expiry = None
        if certificate.valid_until:
            delta = certificate.valid_until - timezone.now()
            days_until_expiry = delta.days
        
        serializer = CertificateStatusSerializer({
            "domain_id": str(domain.id),
            "domain_name": domain.name,
            "has_certificate": True,
            "is_valid": certificate.is_valid,
            "is_expired": certificate.is_expired,
            "days_until_expiry": days_until_expiry,
            "issuer": certificate.issuer,
            "subject": certificate.subject,
            "last_observed": certificate.last_seen,
        })
        
        return Response(serializer.data)
    
    @action(detail=False, methods=["get"])
    def issuer_distribution(self, request):
        """Get distribution of certificate issuers."""
        queryset = self.get_queryset()
        
        # Group by issuer and count
        issuer_data = queryset.values("issuer").annotate(
            count=Count("id")
        ).order_by("-count")
        
        total = queryset.count()
        
        distribution = []
        for item in issuer_data:
            percentage = (item["count"] / total * 100) if total > 0 else 0
            distribution.append({
                "issuer": item["issuer"],
                "count": item["count"],
                "percentage": round(percentage, 2),
            })
        
        serializer = IssuerDistributionSerializer(distribution, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=["get"])
    def changes(self, request):
        """Get certificate changes for a domain."""
        domain_id = request.query_params.get("domain_id")
        if not domain_id:
            return Response({"detail": "domain_id parameter is required"}, status=400)
        
        # Verify user owns the domain
        from apps.dns_intelligence.models import Domain
        try:
            domain = Domain.objects.get(id=domain_id, owner=request.user)
        except Domain.DoesNotExist:
            return Response({"detail": "Domain not found"}, status=404)
        
        # Get certificate observations ordered by time
        observations = CertificateObservation.objects.filter(
            domain=domain
        ).order_by("observed_at")
        
        # Find changes (different fingerprints)
        changes = []
        prev_fingerprint = None
        prev_issuer = None
        
        for obs in observations:
            if prev_fingerprint and obs.fingerprint_sha256 != prev_fingerprint:
                changes.append({
                    "domain_id": str(domain.id),
                    "domain_name": domain.name,
                    "old_fingerprint": prev_fingerprint,
                    "new_fingerprint": obs.fingerprint_sha256,
                    "old_issuer": prev_issuer,
                    "new_issuer": obs.issuer,
                    "changed_at": obs.observed_at,
                })
            
            prev_fingerprint = obs.fingerprint_sha256
            prev_issuer = obs.issuer
        
        serializer = CertificateChangeSerializer(changes, many=True)
        return Response(serializer.data)


class CertificateObservationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for CertificateObservation model (read-only).
    
    Historical observations are immutable, so only read operations are allowed.
    """
    serializer_class = CertificateObservationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["subject", "issuer"]
    ordering_fields = ["observed_at", "valid_until"]
    ordering = ["-observed_at"]
    
    def get_queryset(self):
        """Filter observations by current user."""
        queryset = CertificateObservation.objects.filter(domain__owner=self.request.user)
        
        # Filter by domain if provided
        domain_id = self.request.query_params.get("domain")
        if domain_id:
            queryset = queryset.filter(domain_id=domain_id)
        
        # Filter by certificate fingerprint if provided
        fingerprint = self.request.query_params.get("fingerprint")
        if fingerprint:
            queryset = queryset.filter(fingerprint_sha256=fingerprint)
        
        # Filter by date range
        date_from = self.request.query_params.get("date_from")
        date_to = self.request.query_params.get("date_to")
        if date_from:
            queryset = queryset.filter(observed_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(observed_at__lte=date_to)
        
        return queryset
