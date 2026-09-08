"""
Views for the services app.
"""
from django.db.models import Count, Q
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Service, ServiceObservation
from .serializers import (
    ServiceSerializer,
    ServiceObservationSerializer,
    ServiceAvailabilitySerializer,
    HTTPStatusDistributionSerializer,
    ServiceChangeSerializer,
)


class ServiceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Service model.
    
    Provides CRUD operations for services with filtering by:
    - Asset/domain
    - IP address
    - Port
    - Protocol
    - Service type
    - Availability status
    - Date observed
    """
    serializer_class = ServiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["service_type", "ip_address", "service_banner"]
    ordering_fields = ["last_observed", "port", "service_type"]
    ordering = ["-last_observed"]
    
    def get_queryset(self):
        """Filter services by current user."""
        queryset = Service.objects.filter(domain__owner=self.request.user)
        
        # Filter by domain if provided
        domain_id = self.request.query_params.get("domain")
        if domain_id:
            queryset = queryset.filter(domain_id=domain_id)
        
        # Filter by IP address if provided
        ip_address = self.request.query_params.get("ip_address")
        if ip_address:
            queryset = queryset.filter(ip_address=ip_address)
        
        # Filter by port if provided
        port = self.request.query_params.get("port")
        if port:
            queryset = queryset.filter(port=port)
        
        # Filter by protocol if provided
        protocol = self.request.query_params.get("protocol")
        if protocol:
            queryset = queryset.filter(protocol=protocol)
        
        # Filter by service type if provided
        service_type = self.request.query_params.get("service_type")
        if service_type:
            queryset = queryset.filter(service_type=service_type)
        
        # Filter by availability status
        is_available = self.request.query_params.get("is_available")
        if is_available is not None:
            queryset = queryset.filter(is_available=is_available.lower() == "true")
        
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
        """Get service history for a domain."""
        domain_id = request.query_params.get("domain_id")
        if not domain_id:
            return Response({"detail": "domain_id parameter is required"}, status=400)
        
        # Verify user owns the domain
        from apps.dns_intelligence.models import Domain
        try:
            domain = Domain.objects.get(id=domain_id, owner=request.user)
        except Domain.DoesNotExist:
            return Response({"detail": "Domain not found"}, status=404)
        
        # Get service observations
        observations = ServiceObservation.objects.filter(
            domain=domain
        ).order_by("-observed_at")
        
        page = self.paginate_queryset(observations)
        if page is not None:
            serializer = ServiceObservationSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ServiceObservationSerializer(observations, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=["get"])
    def availability(self, request):
        """Get service availability summary for a domain."""
        domain_id = request.query_params.get("domain_id")
        if not domain_id:
            return Response({"detail": "domain_id parameter is required"}, status=400)
        
        # Verify user owns the domain
        from apps.dns_intelligence.models import Domain
        try:
            domain = Domain.objects.get(id=domain_id, owner=request.user)
        except Domain.DoesNotExist:
            return Response({"detail": "Domain not found"}, status=404)
        
        # Get services for domain
        services = Service.objects.filter(domain=domain)
        
        total = services.count()
        available = services.filter(is_available=True).count()
        unavailable = total - available
        
        availability_percentage = (available / total * 100) if total > 0 else 0
        
        serializer = ServiceAvailabilitySerializer({
            "domain_id": str(domain.id),
            "domain_name": domain.name,
            "total_services": total,
            "available_services": available,
            "unavailable_services": unavailable,
            "availability_percentage": round(availability_percentage, 2),
        })
        
        return Response(serializer.data)
    
    @action(detail=False, methods=["get"])
    def http_status_distribution(self, request):
        """Get distribution of HTTP status codes."""
        queryset = self.get_queryset()
        
        # Filter to only HTTP/HTTPS services with status codes
        queryset = queryset.filter(
            service_type__in=["HTTP", "HTTPS"],
            http_status__isnull=False
        )
        
        # Group by HTTP status and count
        status_data = queryset.values("http_status").annotate(
            count=Count("id")
        ).order_by("-count")
        
        total = queryset.count()
        
        distribution = []
        for item in status_data:
            percentage = (item["count"] / total * 100) if total > 0 else 0
            distribution.append({
                "http_status": item["http_status"],
                "count": item["count"],
                "percentage": round(percentage, 2),
            })
        
        serializer = HTTPStatusDistributionSerializer(distribution, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=["get"])
    def changes(self, request):
        """Get service changes for a domain."""
        domain_id = request.query_params.get("domain_id")
        if not domain_id:
            return Response({"detail": "domain_id parameter is required"}, status=400)
        
        # Verify user owns the domain
        from apps.dns_intelligence.models import Domain
        try:
            domain = Domain.objects.get(id=domain_id, owner=request.user)
        except Domain.DoesNotExist:
            return Response({"detail": "Domain not found"}, status=404)
        
        # Get service observations ordered by time
        observations = ServiceObservation.objects.filter(
            domain=domain
        ).order_by("observed_at")
        
        # Find changes (different availability status)
        changes = []
        prev_status = None
        
        for obs in observations:
            if prev_status is not None and obs.is_available != prev_status:
                changes.append({
                    "domain_id": str(domain.id),
                    "domain_name": domain.name,
                    "ip_address": obs.ip_address,
                    "port": obs.port,
                    "service_type": obs.service_type,
                    "old_status": prev_status,
                    "new_status": obs.is_available,
                    "changed_at": obs.observed_at,
                })
            
            prev_status = obs.is_available
        
        serializer = ServiceChangeSerializer(changes, many=True)
        return Response(serializer.data)


class ServiceObservationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for ServiceObservation model (read-only).
    
    Historical observations are immutable, so only read operations are allowed.
    """
    serializer_class = ServiceObservationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["service_type", "ip_address"]
    ordering_fields = ["observed_at", "port", "service_type"]
    ordering = ["-observed_at"]
    
    def get_queryset(self):
        """Filter observations by current user."""
        queryset = ServiceObservation.objects.filter(domain__owner=self.request.user)
        
        # Filter by domain if provided
        domain_id = self.request.query_params.get("domain")
        if domain_id:
            queryset = queryset.filter(domain_id=domain_id)
        
        # Filter by IP address if provided
        ip_address = self.request.query_params.get("ip_address")
        if ip_address:
            queryset = queryset.filter(ip_address=ip_address)
        
        # Filter by port if provided
        port = self.request.query_params.get("port")
        if port:
            queryset = queryset.filter(port=port)
        
        # Filter by service type if provided
        service_type = self.request.query_params.get("service_type")
        if service_type:
            queryset = queryset.filter(service_type=service_type)
        
        # Filter by availability status
        is_available = self.request.query_params.get("is_available")
        if is_available is not None:
            queryset = queryset.filter(is_available=is_available.lower() == "true")
        
        # Filter by date range
        date_from = self.request.query_params.get("date_from")
        date_to = self.request.query_params.get("date_to")
        if date_from:
            queryset = queryset.filter(observed_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(observed_at__lte=date_to)
        
        return queryset
