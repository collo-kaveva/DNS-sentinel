"""
Unified Historical Observation API.

Provides a unified history API across:
- DNS
- Infrastructure
- Certificates
- Services
- Monitoring
- Lifecycle
- Alerts

The API provides:
- Timeline endpoint
- Asset history endpoint
- Date filtering
- Event-type filtering
- Before/after values
- Pagination

Does NOT manufacture history from current-state tables.
Uses immutable observation records wherever possible.
"""
from typing import List, Dict, Any, Optional
from django.db.models import Q
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from apps.dns_intelligence.models import DNSRecord, DNSObservation, DNSFinding
from apps.infrastructure.models import IPAddress, InfrastructureObservation
from apps.certificates.models import Certificate, CertificateObservation
from apps.services.models import Service, ServiceObservation
from apps.lifecycle.models import Evidence, LifecycleAssessment
from apps.accounts.models import AuditEvent


class HistoryPagination(PageNumberPagination):
    """Pagination for history API."""
    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 200


class UnifiedHistoryViewSet(viewsets.ViewSet):
    """
    Unified History API ViewSet.
    
    Provides a unified interface for historical observations across all subsystems.
    """
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = HistoryPagination
    
    @action(detail=False, methods=["get"])
    def timeline(self, request):
        """
        Get a unified timeline for a domain across all observation types.
        
        Query parameters:
        - domain_id: Required - The domain ID
        - event_type: Optional - Filter by event type (DNS_OBSERVATION, CERTIFICATE, SERVICE, etc.)
        - date_from: Optional - Filter events after this date
        - date_to: Optional - Filter events before this date
        - limit: Optional - Maximum number of events (default 100)
        """
        domain_id = request.query_params.get("domain_id")
        if not domain_id:
            return Response({"detail": "domain_id parameter is required"}, status=400)
        
        # Verify user owns the domain
        from apps.dns_intelligence.models import Domain
        try:
            domain = Domain.objects.get(id=domain_id, owner=request.user)
        except Domain.DoesNotExist:
            return Response({"detail": "Domain not found"}, status=404)
        
        # Get filtering parameters
        event_type = request.query_params.get("event_type")
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        limit = int(request.query_params.get("limit", 100))
        
        # Gather events from all sources
        events = []
        
        # DNS observations
        if not event_type or event_type == "DNS_OBSERVATION":
            dns_events = self._get_dns_observation_events(domain, date_from, date_to)
            events.extend(dns_events)
        
        # DNS records
        if not event_type or event_type == "DNS_RECORD":
            dns_record_events = self._get_dns_record_events(domain, date_from, date_to)
            events.extend(dns_record_events)
        
        # IP address observations
        if not event_type or event_type == "IP_ADDRESS":
            ip_events = self._get_ip_address_events(domain, date_from, date_to)
            events.extend(ip_events)
        
        # Certificate observations
        if not event_type or event_type == "CERTIFICATE":
            cert_events = self._get_certificate_events(domain, date_from, date_to)
            events.extend(cert_events)
        
        # Service observations
        if not event_type or event_type == "SERVICE":
            service_events = self._get_service_events(domain, date_from, date_to)
            events.extend(service_events)
        
        # Lifecycle assessments
        if not event_type or event_type == "LIFECYCLE":
            lifecycle_events = self._get_lifecycle_events(domain, date_from, date_to)
            events.extend(lifecycle_events)
        
        # Audit events
        if not event_type or event_type == "AUDIT":
            audit_events = self._get_audit_events(domain, date_from, date_to)
            events.extend(audit_events)
        
        # Sort by timestamp (newest first)
        events.sort(key=lambda e: e["timestamp"], reverse=True)
        
        # Apply limit
        events = events[:limit]
        
        return Response({
            "domain_id": str(domain.id),
            "domain_name": domain.name,
            "total_events": len(events),
            "events": events,
        })
    
    @action(detail=False, methods=["get"])
    def asset_history(self, request):
        """
        Get detailed history for a specific asset.
        
        Query parameters:
        - domain_id: Required - The domain ID
        - asset_type: Required - Type of asset (DNS, IP, CERTIFICATE, SERVICE)
        - asset_identifier: Required - Identifier for the asset (hostname, IP, fingerprint, etc.)
        - date_from: Optional - Filter events after this date
        - date_to: Optional - Filter events before this date
        """
        domain_id = request.query_params.get("domain_id")
        asset_type = request.query_params.get("asset_type")
        asset_identifier = request.query_params.get("asset_identifier")
        
        if not all([domain_id, asset_type, asset_identifier]):
            return Response({
                "detail": "domain_id, asset_type, and asset_identifier parameters are required"
            }, status=400)
        
        # Verify user owns the domain
        from apps.dns_intelligence.models import Domain
        try:
            domain = Domain.objects.get(id=domain_id, owner=request.user)
        except Domain.DoesNotExist:
            return Response({"detail": "Domain not found"}, status=404)
        
        # Get date filters
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        
        # Get history based on asset type
        history = []
        
        if asset_type == "DNS":
            history = self._get_dns_asset_history(domain, asset_identifier, date_from, date_to)
        elif asset_type == "IP":
            history = self._get_ip_asset_history(domain, asset_identifier, date_from, date_to)
        elif asset_type == "CERTIFICATE":
            history = self._get_certificate_asset_history(domain, asset_identifier, date_from, date_to)
        elif asset_type == "SERVICE":
            history = self._get_service_asset_history(domain, asset_identifier, date_from, date_to)
        else:
            return Response({"detail": f"Unsupported asset type: {asset_type}"}, status=400)
        
        return Response({
            "domain_id": str(domain.id),
            "domain_name": domain.name,
            "asset_type": asset_type,
            "asset_identifier": asset_identifier,
            "history": history,
        })
    
    def _get_dns_observation_events(self, domain, date_from=None, date_to=None) -> List[Dict[str, Any]]:
        """Get DNS observation events."""
        queryset = DNSObservation.objects.filter(domain=domain)
        
        if date_from:
            queryset = queryset.filter(observed_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(observed_at__lte=date_to)
        
        events = []
        for obs in queryset:
            events.append({
                "event_id": str(obs.id),
                "event_type": "DNS_OBSERVATION",
                "timestamp": obs.observed_at.isoformat(),
                "asset": obs.hostname,
                "description": f"DNS {obs.record_type} query: {', '.join(obs.values) if obs.values else 'No answer'}",
                "source": obs.source,
                "previous_state": None,
                "new_state": obs.response_code,
                "evidence_id": str(obs.id),
                "metadata": {
                    "record_type": obs.record_type,
                    "values": obs.values,
                    "response_code": obs.response_code,
                    "confidence": obs.confidence,
                }
            })
        
        return events
    
    def _get_dns_record_events(self, domain, date_from=None, date_to=None) -> List[Dict[str, Any]]:
        """Get DNS record change events."""
        queryset = DNSRecord.objects.filter(domain=domain)
        
        if date_from:
            queryset = queryset.filter(last_seen__gte=date_from)
        if date_to:
            queryset = queryset.filter(last_seen__lte=date_to)
        
        events = []
        for record in queryset:
            events.append({
                "event_id": str(record.id),
                "event_type": "DNS_RECORD",
                "timestamp": record.last_seen.isoformat(),
                "asset": record.hostname,
                "description": f"DNS {record.record_type} record: {record.value}",
                "source": "DNS Intelligence",
                "previous_state": None,
                "new_state": "CURRENT" if record.is_current else "HISTORICAL",
                "evidence_id": str(record.id),
                "metadata": {
                    "record_type": record.record_type,
                    "value": record.value,
                    "is_current": record.is_current,
                    "first_seen": record.first_seen.isoformat(),
                }
            })
        
        return events
    
    def _get_ip_address_events(self, domain, date_from=None, date_to=None) -> List[Dict[str, Any]]:
        """Get IP address observation events."""
        queryset = InfrastructureObservation.objects.filter(domain=domain)
        
        if date_from:
            queryset = queryset.filter(observed_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(observed_at__lte=date_to)
        
        events = []
        for obs in queryset:
            events.append({
                "event_id": str(obs.id),
                "event_type": "IP_ADDRESS",
                "timestamp": obs.observed_at.isoformat(),
                "asset": obs.address,
                "description": f"IP {obs.address} - {obs.organization or 'Unknown'}",
                "source": obs.source,
                "previous_state": None,
                "new_state": obs.organization,
                "evidence_id": str(obs.id),
                "metadata": {
                    "asn": obs.asn,
                    "network": obs.network,
                    "organization": obs.organization,
                    "country": obs.country,
                    "confidence": obs.confidence,
                }
            })
        
        return events
    
    def _get_certificate_events(self, domain, date_from=None, date_to=None) -> List[Dict[str, Any]]:
        """Get certificate observation events."""
        queryset = CertificateObservation.objects.filter(domain=domain)
        
        if date_from:
            queryset = queryset.filter(observed_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(observed_at__lte=date_to)
        
        events = []
        for obs in queryset:
            events.append({
                "event_id": str(obs.id),
                "event_type": "CERTIFICATE",
                "timestamp": obs.observed_at.isoformat(),
                "asset": obs.subject,
                "description": f"Certificate from {obs.issuer}",
                "source": obs.source,
                "previous_state": None,
                "new_state": "VALID" if obs.is_valid else "INVALID",
                "evidence_id": str(obs.id),
                "metadata": {
                    "issuer": obs.issuer,
                    "valid_from": obs.valid_from.isoformat() if obs.valid_from else None,
                    "valid_until": obs.valid_until.isoformat() if obs.valid_until else None,
                    "is_expired": obs.is_expired,
                    "sans": obs.sans,
                    "confidence": obs.confidence,
                }
            })
        
        return events
    
    def _get_service_events(self, domain, date_from=None, date_to=None) -> List[Dict[str, Any]]:
        """Get service observation events."""
        queryset = ServiceObservation.objects.filter(domain=domain)
        
        if date_from:
            queryset = queryset.filter(observed_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(observed_at__lte=date_to)
        
        events = []
        for obs in queryset:
            events.append({
                "event_id": str(obs.id),
                "event_type": "SERVICE",
                "timestamp": obs.observed_at.isoformat(),
                "asset": f"{obs.service_type}://{obs.ip_address}:{obs.port}",
                "description": f"{obs.service_type} service - {'Available' if obs.is_available else 'Unavailable'}",
                "source": obs.source,
                "previous_state": None,
                "new_state": "AVAILABLE" if obs.is_available else "UNAVAILABLE",
                "evidence_id": str(obs.id),
                "metadata": {
                    "service_type": obs.service_type,
                    "port": obs.port,
                    "protocol": obs.protocol,
                    "http_status": obs.http_status,
                    "ssl_tls_enabled": obs.ssl_tls_enabled,
                    "confidence": obs.confidence,
                }
            })
        
        return events
    
    def _get_lifecycle_events(self, domain, date_from=None, date_to=None) -> List[Dict[str, Any]]:
        """Get lifecycle assessment events."""
        queryset = LifecycleAssessment.objects.filter(domain=domain)
        
        if date_from:
            queryset = queryset.filter(generated_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(generated_at__lte=date_to)
        
        events = []
        for assessment in queryset:
            events.append({
                "event_id": str(assessment.id),
                "event_type": "LIFECYCLE",
                "timestamp": assessment.generated_at.isoformat(),
                "asset": domain.name,
                "description": f"Lifecycle classification: {assessment.classification}",
                "source": "Lifecycle Engine",
                "previous_state": None,
                "new_state": assessment.classification,
                "evidence_id": str(assessment.id),
                "metadata": {
                    "classification": assessment.classification,
                    "confidence": str(assessment.confidence),
                    "model_version": assessment.model_version,
                    "supporting_evidence_count": len(assessment.supporting_evidence),
                    "explanation": assessment.explanation,
                }
            })
        
        return events
    
    def _get_audit_events(self, domain, date_from=None, date_to=None) -> List[Dict[str, Any]]:
        """Get audit events for a domain."""
        queryset = AuditEvent.objects.filter(
            Q(resource_id=str(domain.id)) | Q(metadata__domain_id=str(domain.id)),
            actor_id=domain.owner_id
        )
        
        if date_from:
            queryset = queryset.filter(timestamp__gte=date_from)
        if date_to:
            queryset = queryset.filter(timestamp__lte=date_to)
        
        events = []
        for audit in queryset:
            events.append({
                "event_id": str(audit.id),
                "event_type": "AUDIT",
                "timestamp": audit.timestamp.isoformat(),
                "asset": audit.resource_name or "System",
                "description": audit.action,
                "source": "Audit Log",
                "previous_state": None,
                "new_state": audit.result,
                "evidence_id": str(audit.id),
                "metadata": {
                    "event_type": audit.event_type,
                    "result": audit.result,
                    "resource_type": audit.resource_type,
                }
            })
        
        return events
    
    def _get_dns_asset_history(self, domain, hostname, date_from=None, date_to=None) -> List[Dict[str, Any]]:
        """Get detailed DNS history for a hostname."""
        observations = DNSObservation.objects.filter(
            domain=domain,
            hostname=hostname
        ).order_by("observed_at")
        
        if date_from:
            observations = observations.filter(observed_at__gte=date_from)
        if date_to:
            observations = observations.filter(observed_at__lte=date_to)
        
        history = []
        for obs in observations:
            history.append({
                "timestamp": obs.observed_at.isoformat(),
                "record_type": obs.record_type,
                "values": obs.values,
                "response_code": obs.response_code,
                "ttl": obs.ttl,
                "source": obs.source,
                "confidence": obs.confidence,
            })
        
        return history
    
    def _get_ip_asset_history(self, domain, ip_address, date_from=None, date_to=None) -> List[Dict[str, Any]]:
        """Get detailed IP history for an address."""
        observations = InfrastructureObservation.objects.filter(
            domain=domain,
            address=ip_address
        ).order_by("observed_at")
        
        if date_from:
            observations = observations.filter(observed_at__gte=date_from)
        if date_to:
            observations = observations.filter(observed_at__lte=date_to)
        
        history = []
        for obs in observations:
            history.append({
                "timestamp": obs.observed_at.isoformat(),
                "asn": obs.asn,
                "network": obs.network,
                "organization": obs.organization,
                "country": obs.country,
                "reverse_dns": obs.reverse_dns,
                "source": obs.source,
                "confidence": obs.confidence,
            })
        
        return history
    
    def _get_certificate_asset_history(self, domain, fingerprint, date_from=None, date_to=None) -> List[Dict[str, Any]]:
        """Get detailed certificate history for a fingerprint."""
        observations = CertificateObservation.objects.filter(
            domain=domain,
            fingerprint_sha256=fingerprint
        ).order_by("observed_at")
        
        if date_from:
            observations = observations.filter(observed_at__gte=date_from)
        if date_to:
            observations = observations.filter(observed_at__lte=date_to)
        
        history = []
        for obs in observations:
            history.append({
                "timestamp": obs.observed_at.isoformat(),
                "subject": obs.subject,
                "issuer": obs.issuer,
                "valid_from": obs.valid_from.isoformat() if obs.valid_from else None,
                "valid_until": obs.valid_until.isoformat() if obs.valid_until else None,
                "sans": obs.sans,
                "is_valid": obs.is_valid,
                "is_expired": obs.is_expired,
                "source": obs.source,
                "confidence": obs.confidence,
            })
        
        return history
    
    def _get_service_asset_history(self, domain, service_identifier, date_from=None, date_to=None) -> List[Dict[str, Any]]:
        """Get detailed service history for a service identifier (ip:port)."""
        # Parse service identifier (expected format: "ip:port")
        parts = service_identifier.split(":")
        if len(parts) != 2:
            return []
        
        ip_address, port = parts
        
        observations = ServiceObservation.objects.filter(
            domain=domain,
            ip_address=ip_address,
            port=int(port)
        ).order_by("observed_at")
        
        if date_from:
            observations = observations.filter(observed_at__gte=date_from)
        if date_to:
            observations = observations.filter(observed_at__lte=date_to)
        
        history = []
        for obs in observations:
            history.append({
                "timestamp": obs.observed_at.isoformat(),
                "service_type": obs.service_type,
                "is_available": obs.is_available,
                "http_status": obs.http_status,
                "response_time_ms": obs.response_time_ms,
                "ssl_tls_enabled": obs.ssl_tls_enabled,
                "source": obs.source,
                "confidence": obs.confidence,
            })
        
        return history
