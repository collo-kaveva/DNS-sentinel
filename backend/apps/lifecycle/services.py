"""
Evidence service for creating and managing evidence from observations.

This service bridges existing observation models (DNS, infrastructure, etc.)
with the unified evidence system for lifecycle classification.
"""
from typing import List, Dict, Any, Optional
from django.utils import timezone

from .models import Evidence, EvidenceRelationship, EvidenceType, EvidenceStatus, Confidence


class EvidenceService:
    """Service for creating and managing evidence."""
    
    @staticmethod
    def create_from_dns_observation(dns_observation, domain) -> Evidence:
        """Create evidence from a DNS observation."""
        return Evidence.objects.create(
            domain=domain,
            owner=domain.owner,
            evidence_type=EvidenceType.DNS_OBSERVATION,
            status=EvidenceStatus.OBSERVED,
            confidence=Confidence.HIGH if dns_observation.confidence == "HIGH" else Confidence.MEDIUM,
            source=dns_observation.source,
            collection_method="DNS Resolver",
            observation=f"{dns_observation.hostname} ({dns_observation.record_type}): {', '.join(dns_observation.values)}",
            entity_name=dns_observation.hostname,
            entity_type="domain",
            related_object_id=dns_observation.id,
            related_object_type="dns_intelligence.DNSObservation",
            metadata={
                "record_type": dns_observation.record_type,
                "values": dns_observation.values,
                "response_code": dns_observation.response_code,
                "ttl": dns_observation.ttl,
                "resolver_used": dns_observation.resolver_used,
                "query_time_ms": dns_observation.query_time_ms,
                "dnssec_signed": dns_observation.dnssec_signed,
            },
            observed_at=dns_observation.observed_at,
        )
    
    @staticmethod
    def create_from_dns_record(dns_record, domain) -> Evidence:
        """Create evidence from a DNS record."""
        status = EvidenceStatus.OBSERVED if dns_record.is_current else EvidenceStatus.HISTORICAL
        return Evidence.objects.create(
            domain=domain,
            owner=domain.owner,
            evidence_type=EvidenceType.DNS_RECORD,
            status=status,
            confidence=Confidence.HIGH,
            source="DNS Intelligence",
            collection_method="DNS Resolver",
            observation=f"{dns_record.hostname} ({dns_record.record_type}): {dns_record.value}",
            entity_name=dns_record.hostname,
            entity_type="domain",
            related_object_id=dns_record.id,
            related_object_type="dns_intelligence.DNSRecord",
            metadata={
                "record_type": dns_record.record_type,
                "value": dns_record.value,
                "ttl": dns_record.ttl,
                "is_current": dns_record.is_current,
            },
            observed_at=dns_record.last_seen,
        )
    
    @staticmethod
    def create_from_ip_address(ip_address, domain) -> Evidence:
        """Create evidence from an IP address."""
        confidence = Confidence.MEDIUM
        if ip_address.rdap_available and ip_address.association_status == "CURRENT":
            confidence = Confidence.HIGH
        elif not ip_address.rdap_available:
            confidence = Confidence.LOW
        
        status_map = {
            "CURRENT": EvidenceStatus.OBSERVED,
            "HISTORICAL": EvidenceStatus.HISTORICAL,
            "ESTIMATED": EvidenceStatus.INFERRED,
            "UNKNOWN": EvidenceStatus.UNKNOWN,
        }
        
        return Evidence.objects.create(
            domain=domain,
            owner=domain.owner,
            evidence_type=EvidenceType.IP_ADDRESS,
            status=status_map.get(ip_address.association_status, EvidenceStatus.UNKNOWN),
            confidence=confidence,
            source="RDAP" if ip_address.rdap_available else "DNS Resolution",
            collection_method="Infrastructure Analysis",
            observation=f"IP {ip_address.address} ({ip_address.version}) associated with domain",
            entity_name=ip_address.address,
            entity_type="ip_address",
            related_object_id=ip_address.id,
            related_object_type="infrastructure.IPAddress",
            metadata={
                "version": ip_address.version,
                "association_status": ip_address.association_status,
                "reverse_dns": ip_address.reverse_dns,
                "asn": ip_address.asn,
                "network": ip_address.network,
                "organization": ip_address.organization,
                "country": ip_address.country,
                "is_likely_cdn": ip_address.is_likely_cdn,
                "is_likely_shared_hosting": ip_address.is_likely_shared_hosting,
                "cdn_indicator_source": ip_address.cdn_indicator_source,
                "rdap_available": ip_address.rdap_available,
            },
            observed_at=ip_address.last_seen,
        )
    
    @staticmethod
    def create_ip_domain_relationship(ip_evidence: Evidence, domain_evidence: Evidence, relationship_type: str = "resolves_to") -> EvidenceRelationship:
        """Create a relationship between IP and domain evidence."""
        return EvidenceRelationship.objects.create(
            from_evidence=domain_evidence,
            to_evidence=ip_evidence,
            relationship_type=relationship_type,
            confidence=domain_evidence.confidence,
        )
    
    @staticmethod
    def create_analyst_note(domain, content, author) -> Evidence:
        """Create an analyst note as evidence."""
        return Evidence.objects.create(
            domain=domain,
            owner=domain.owner,
            evidence_type=EvidenceType.ANALYST_NOTE,
            status=EvidenceStatus.ANALYST,
            confidence=Confidence.HIGH,
            source="Analyst",
            collection_method="Manual Entry",
            observation=content,
            entity_name=domain.name,
            entity_type="domain",
            metadata={
                "author_id": str(author.id),
                "author_username": author.username,
            },
        )
    
    @staticmethod
    def create_from_certificate_observation(cert_observation, domain) -> Evidence:
        """Create evidence from a certificate observation."""
        status = EvidenceStatus.OBSERVED if cert_observation.is_valid else EvidenceStatus.HISTORICAL
        if cert_observation.is_expired:
            status = EvidenceStatus.HISTORICAL
        
        return Evidence.objects.create(
            domain=domain,
            owner=domain.owner,
            evidence_type=EvidenceType.CERTIFICATE,
            status=status,
            confidence=Confidence.HIGH if cert_observation.confidence == "HIGH" else Confidence.MEDIUM,
            source=cert_observation.source,
            collection_method=cert_observation.collection_method or "TLS Handshake",
            observation=f"Certificate from {cert_observation.issuer} for {cert_observation.subject}",
            entity_name=cert_observation.subject,
            entity_type="certificate",
            related_object_id=cert_observation.id,
            related_object_type="certificates.CertificateObservation",
            metadata={
                "issuer": cert_observation.issuer,
                "subject": cert_observation.subject,
                "serial_number": cert_observation.serial_number,
                "fingerprint_sha256": cert_observation.fingerprint_sha256,
                "valid_from": cert_observation.valid_from.isoformat() if cert_observation.valid_from else None,
                "valid_until": cert_observation.valid_until.isoformat() if cert_observation.valid_until else None,
                "sans": cert_observation.sans,
                "is_valid": cert_observation.is_valid,
                "is_expired": cert_observation.is_expired,
                "is_self_signed": cert_observation.is_self_signed,
                "public_key_algorithm": cert_observation.public_key_algorithm,
                "public_key_size": cert_observation.public_key_size,
            },
            observed_at=cert_observation.observed_at,
        )
    
    @staticmethod
    def create_from_service_observation(service_observation, domain) -> Evidence:
        """Create evidence from a service observation."""
        status = EvidenceStatus.OBSERVED if service_observation.is_available else EvidenceStatus.HISTORICAL
        
        return Evidence.objects.create(
            domain=domain,
            owner=domain.owner,
            evidence_type=EvidenceType.SERVICE,
            status=status,
            confidence=Confidence.MEDIUM if service_observation.confidence == "HIGH" else Confidence.LOW,
            source=service_observation.source,
            collection_method=service_observation.collection_method or "Service Observation",
            observation=f"{service_observation.service_type} service at {service_observation.ip_address}:{service_observation.port} - {'Available' if service_observation.is_available else 'Unavailable'}",
            entity_name=f"{service_observation.service_type}://{service_observation.ip_address}:{service_observation.port}",
            entity_type="service",
            related_object_id=service_observation.id,
            related_object_type="services.ServiceObservation",
            metadata={
                "service_type": service_observation.service_type,
                "ip_address": service_observation.ip_address,
                "port": service_observation.port,
                "protocol": service_observation.protocol,
                "is_available": service_observation.is_available,
                "http_status": service_observation.http_status,
                "response_time_ms": service_observation.response_time_ms,
                "ssl_tls_enabled": service_observation.ssl_tls_enabled,
                "service_banner": service_observation.service_banner,
            },
            observed_at=service_observation.observed_at,
        )
    
    @staticmethod
    def create_from_lifecycle_assessment(assessment, domain) -> Evidence:
        """Create evidence from a lifecycle assessment."""
        return Evidence.objects.create(
            domain=domain,
            owner=domain.owner,
            evidence_type=EvidenceType.LIFECYCLE_ASSESSMENT,
            status=EvidenceStatus.ANALYST,
            confidence=Confidence.HIGH if assessment.confidence >= 0.75 else Confidence.MEDIUM,
            source="Lifecycle Engine",
            collection_method="Rule-based Classification",
            observation=f"Lifecycle classification: {assessment.classification} (confidence: {assessment.confidence})",
            entity_name=domain.name,
            entity_type="domain",
            related_object_id=assessment.id,
            related_object_type="lifecycle.LifecycleAssessment",
            metadata={
                "classification": assessment.classification,
                "confidence": str(assessment.confidence),
                "model_version": assessment.model_version,
                "supporting_evidence": assessment.supporting_evidence,
                "contradicting_evidence": assessment.contradicting_evidence,
                "limitations": assessment.limitations,
                "explanation": assessment.explanation,
            },
            observed_at=assessment.generated_at,
        )
    
    @staticmethod
    def get_evidence_for_domain(domain_id: str, evidence_type: Optional[str] = None) -> List[Evidence]:
        """Get all evidence for a domain, optionally filtered by type."""
        queryset = Evidence.objects.filter(domain_id=domain_id)
        if evidence_type:
            queryset = queryset.filter(evidence_type=evidence_type)
        return list(queryset)
    
    @staticmethod
    def get_evidence_timeline(domain_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get a chronological timeline of evidence for a domain."""
        evidence = Evidence.objects.filter(domain_id=domain_id).order_by("observed_at")[:limit]
        
        timeline = []
        for ev in evidence:
            timeline.append({
                "id": str(ev.id),
                "event_type": ev.evidence_type,
                "timestamp": ev.observed_at.isoformat(),
                "asset": ev.entity_name or ev.domain.name,
                "observation": ev.observation,
                "source": ev.source,
                "confidence": ev.confidence,
                "status": ev.status,
                "metadata": ev.metadata,
            })
        
        return timeline


def sync_domain_evidence(domain) -> Dict[str, int]:
    """
    Sync all existing observations for a domain into the evidence system.
    
    This creates evidence items from existing DNS records, DNS observations,
    IP addresses, certificates, services, and establishes relationships between them.
    
    Returns a summary of what was created.
    """
    from apps.dns_intelligence.models import DNSRecord, DNSObservation
    from apps.infrastructure.models import IPAddress
    from apps.certificates.models import CertificateObservation
    from apps.services.models import ServiceObservation
    
    summary = {
        "dns_records": 0,
        "dns_observations": 0,
        "ip_addresses": 0,
        "certificates": 0,
        "services": 0,
        "relationships": 0,
    }
    
    # Create evidence from DNS records
    dns_records = DNSRecord.objects.filter(domain=domain)
    for record in dns_records:
        EvidenceService.create_from_dns_record(record, domain)
        summary["dns_records"] += 1
    
    # Create evidence from DNS observations
    dns_observations = DNSObservation.objects.filter(domain=domain)
    for obs in dns_observations:
        EvidenceService.create_from_dns_observation(obs, domain)
        summary["dns_observations"] += 1
    
    # Create evidence from IP addresses
    ip_addresses = IPAddress.objects.filter(domain=domain)
    ip_evidence_map = {}
    for ip in ip_addresses:
        ip_evidence = EvidenceService.create_from_ip_address(ip, domain)
        ip_evidence_map[str(ip.id)] = ip_evidence
        summary["ip_addresses"] += 1
    
    # Create evidence from certificate observations
    cert_observations = CertificateObservation.objects.filter(domain=domain)
    for cert in cert_observations:
        EvidenceService.create_from_certificate_observation(cert, domain)
        summary["certificates"] += 1
    
    # Create evidence from service observations
    service_observations = ServiceObservation.objects.filter(domain=domain)
    for service in service_observations:
        EvidenceService.create_from_service_observation(service, domain)
        summary["services"] += 1
    
    # Create relationships between domain and IPs
    domain_evidence = Evidence.objects.filter(
        domain=domain,
        evidence_type=EvidenceType.DNS_RECORD,
        entity_name=domain.name
    ).first()
    
    if domain_evidence:
        for ip in ip_addresses:
            ip_evidence = ip_evidence_map.get(str(ip.id))
            if ip_evidence:
                EvidenceService.create_ip_domain_relationship(domain_evidence, ip_evidence)
                summary["relationships"] += 1
    
    return summary
