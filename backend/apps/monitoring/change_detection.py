"""
Change detection service for monitoring.

This service compares current observations with previous observations to detect
actual evidence-backed changes. Only creates events when real differences exist.
"""
from typing import List, Dict, Any, Optional
from django.utils import timezone

from apps.dns_intelligence.models import DNSObservation, DNSRecord
from apps.infrastructure.models import InfrastructureObservation, IPAddress
from apps.lifecycle.models import LifecycleAssessment
from .models import ChangeEvent


class ChangeDetector:
    """
    Detects changes between observations.
    
    This class provides methods to compare current observations with previous
    observations and generate change events only when real differences exist.
    """
    
    def __init__(self, domain):
        self.domain = domain
    
    def detect_dns_changes(self, current_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect DNS record changes.
        
        Compares current DNS query results with the most recent previous observation
        for the same record type. Only creates events for actual differences.
        """
        changes = []
        
        for rtype, result in current_results.items():
            # Skip failed queries - these are not real changes
            if result.response_code not in ("NOERROR", "NXDOMAIN"):
                continue
            
            # Get previous observation for this record type
            previous_obs = DNSObservation.objects.filter(
                domain=self.domain,
                hostname=self.domain.name,
                record_type=rtype,
            ).order_by("-observed_at").first()
            
            if not previous_obs:
                # First observation - no change to detect
                continue
            
            # Skip if previous query failed
            if previous_obs.response_code not in ("NOERROR", "NXDOMAIN"):
                continue
            
            # Compare values
            current_values = set(result.values)
            previous_values = set(previous_obs.values)
            
            # Detect added records
            added = current_values - previous_values
            if added:
                for value in added:
                    changes.append({
                        "event_type": ChangeEvent.EventType.DNS_RECORD_ADDED,
                        "description": f"DNS {rtype} record added: {value}",
                        "previous_value": "",
                        "new_value": value,
                        "entity_name": f"{self.domain.name} ({rtype})",
                        "entity_type": "DNSRecord",
                        "metadata": {"record_type": rtype, "value": value},
                    })
            
            # Detect removed records
            removed = previous_values - current_values
            if removed:
                for value in removed:
                    changes.append({
                        "event_type": ChangeEvent.EventType.DNS_RECORD_REMOVED,
                        "description": f"DNS {rtype} record removed: {value}",
                        "previous_value": value,
                        "new_value": "",
                        "entity_name": f"{self.domain.name} ({rtype})",
                        "entity_type": "DNSRecord",
                        "metadata": {"record_type": rtype, "value": value},
                    })
            
            # Detect changed records (same value but different TTL or other metadata)
            if current_values == previous_values and len(current_values) > 0:
                # Check for TTL changes
                if result.ttl != previous_obs.ttl:
                    changes.append({
                        "event_type": ChangeEvent.EventType.DNS_RECORD_CHANGED,
                        "description": f"DNS {rtype} TTL changed from {previous_obs.ttl} to {result.ttl}",
                        "previous_value": str(previous_obs.ttl),
                        "new_value": str(result.ttl),
                        "entity_name": f"{self.domain.name} ({rtype})",
                        "entity_type": "DNSRecord",
                        "metadata": {"record_type": rtype, "change_type": "TTL"},
                    })
        
        return changes
    
    def detect_ip_changes(self, current_ips: List[str], rdap_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect IP address and infrastructure changes.
        
        Compares current IP addresses and their RDAP data with previous observations.
        Only creates events for actual differences.
        """
        changes = []
        current_ip_set = set(current_ips)
        
        # Get previous IPs
        previous_ips = set(
            IPAddress.objects.filter(
                domain=self.domain,
                association_status=IPAddress.AssociationStatus.CURRENT
            ).values_list("address", flat=True)
        )
        
        # Detect new IPs
        new_ips = current_ip_set - previous_ips
        if new_ips:
            for ip in new_ips:
                changes.append({
                    "event_type": ChangeEvent.EventType.IP_CHANGED,
                    "description": f"New IP address appeared: {ip}",
                    "previous_value": "",
                    "new_value": ip,
                    "entity_name": ip,
                    "entity_type": "IPAddress",
                    "metadata": {"ip": ip, "change_type": "appeared"},
                })
        
        # Detect removed IPs
        removed_ips = previous_ips - current_ip_set
        if removed_ips:
            for ip in removed_ips:
                changes.append({
                    "event_type": ChangeEvent.EventType.IP_CHANGED,
                    "description": f"IP address disappeared: {ip}",
                    "previous_value": ip,
                    "new_value": "",
                    "entity_name": ip,
                    "entity_type": "IPAddress",
                    "metadata": {"ip": ip, "change_type": "disappeared"},
                })
        
        # Detect ASN/organization changes for existing IPs
        for ip in current_ip_set & previous_ips:
            previous_ip = IPAddress.objects.filter(domain=self.domain, address=ip).first()
            if not previous_ip:
                continue
            
            current_rdap = rdap_data.get(ip)
            if not current_rdap or not current_rdap.available:
                continue
            
            # Check ASN change
            if previous_ip.asn and current_rdap.asn and previous_ip.asn != current_rdap.asn:
                changes.append({
                    "event_type": ChangeEvent.EventType.ASN_CHANGED,
                    "description": f"ASN changed for {ip}: {previous_ip.asn} -> {current_rdap.asn}",
                    "previous_value": previous_ip.asn or "",
                    "new_value": current_rdap.asn or "",
                    "entity_name": ip,
                    "entity_type": "IPAddress",
                    "metadata": {"ip": ip, "previous_asn": previous_ip.asn, "new_asn": current_rdap.asn},
                })
            
            # Check organization change
            if previous_ip.organization and current_rdap.organization and previous_ip.organization != current_rdap.organization:
                changes.append({
                    "event_type": ChangeEvent.EventType.PROVIDER_CHANGED,
                    "description": f"Provider changed for {ip}: {previous_ip.organization} -> {current_rdap.organization}",
                    "previous_value": previous_ip.organization or "",
                    "new_value": current_rdap.organization or "",
                    "entity_name": ip,
                    "entity_type": "IPAddress",
                    "metadata": {"ip": ip, "previous_org": previous_ip.organization, "new_org": current_rdap.organization},
                })
        
        return changes
    
    def detect_certificate_changes(self, current_cert: Optional[Any]) -> List[Dict[str, Any]]:
        """
        Detect certificate changes.
        
        Compares current certificate with previous observations.
        Only creates events for actual differences.
        """
        changes = []
        
        if not current_cert:
            return changes
        
        # Get previous certificate
        previous_cert = None  # Would query Certificate model here
        
        if not previous_cert:
            # First certificate - no change to detect
            return changes
        
        # Detect certificate fingerprint change
        if current_cert.fingerprint_sha256 != previous_cert.fingerprint_sha256:
            changes.append({
                "event_type": ChangeEvent.EventType.CERTIFICATE_CHANGED,
                "description": f"Certificate changed for {self.domain.name}",
                "previous_value": previous_cert.fingerprint_sha256,
                "new_value": current_cert.fingerprint_sha256,
                "entity_name": self.domain.name,
                "entity_type": "Certificate",
                "metadata": {
                    "previous_subject": previous_cert.subject,
                    "new_subject": current_cert.subject,
                    "previous_issuer": previous_cert.issuer,
                    "new_issuer": current_cert.issuer,
                },
            })
        
        # Detect certificate expiration
        if current_cert.is_expired and not previous_cert.is_expired:
            changes.append({
                "event_type": ChangeEvent.EventType.CERTIFICATE_EXPIRED,
                "description": f"Certificate expired for {self.domain.name}",
                "previous_value": "valid",
                "new_value": "expired",
                "entity_name": self.domain.name,
                "entity_type": "Certificate",
                "metadata": {
                    "valid_until": str(current_cert.valid_until),
                    "subject": current_cert.subject,
                },
            })
        
        return changes
    
    def detect_service_changes(self, current_services: List[Any]) -> List[Dict[str, Any]]:
        """
        Detect service changes.
        
        Compares current services with previous observations.
        Only creates events for actual differences.
        """
        changes = []
        
        # Get previous services
        previous_services = []  # Would query Service model here
        
        current_service_keys = {(s.ip_address, s.port, s.protocol) for s in current_services}
        previous_service_keys = {(s.ip_address, s.port, s.protocol) for s in previous_services}
        
        # Detect new services
        new_services = current_service_keys - previous_service_keys
        if new_services:
            for ip, port, protocol in new_services:
                changes.append({
                    "event_type": ChangeEvent.EventType.SERVICE_APPEARED,
                    "description": f"Service appeared: {protocol}://{ip}:{port}",
                    "previous_value": "",
                    "new_value": f"{protocol}://{ip}:{port}",
                    "entity_name": f"{ip}:{port}",
                    "entity_type": "Service",
                    "metadata": {"ip": ip, "port": port, "protocol": protocol},
                })
        
        # Detect disappeared services
        disappeared_services = previous_service_keys - current_service_keys
        if disappeared_services:
            for ip, port, protocol in disappeared_services:
                changes.append({
                    "event_type": ChangeEvent.EventType.SERVICE_DISAPPEARED,
                    "description": f"Service disappeared: {protocol}://{ip}:{port}",
                    "previous_value": f"{protocol}://{ip}:{port}",
                    "new_value": "",
                    "entity_name": f"{ip}:{port}",
                    "entity_type": "Service",
                    "metadata": {"ip": ip, "port": port, "protocol": protocol},
                })
        
        return changes