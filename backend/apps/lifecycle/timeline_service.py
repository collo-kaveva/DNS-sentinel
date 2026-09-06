"""
Timeline service for aggregating historical events across all observation types.

This service provides a unified timeline view by aggregating events from:
- DNS observations and records
- IP address observations
- Certificate observations (when implemented)
- Service observations (when implemented)
- Audit events
- Investigation events
- Lifecycle assessments

Each event contains:
- Event ID
- Event type
- Timestamp
- Asset
- Previous state where available
- New state where available
- Source
- Evidence reference
"""
from typing import List, Dict, Any, Optional
from django.db.models import Q

from apps.dns_intelligence.models import DNSRecord, DNSObservation, DNSFinding
from apps.infrastructure.models import IPAddress
from apps.investigation.models import Investigation, AnalystNote
from apps.lifecycle.models import Evidence, LifecycleAssessment
from apps.accounts.models import AuditEvent


class TimelineEvent:
    """Represents a single timeline event."""
    
    def __init__(
        self,
        event_id: str,
        event_type: str,
        timestamp: str,
        asset: str,
        description: str,
        source: str,
        previous_state: Optional[str] = None,
        new_state: Optional[str] = None,
        evidence_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.event_id = event_id
        self.event_type = event_type
        self.timestamp = timestamp
        self.asset = asset
        self.description = description
        self.source = source
        self.previous_state = previous_state
        self.new_state = new_state
        self.evidence_id = evidence_id
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "asset": self.asset,
            "description": self.description,
            "source": self.source,
            "previous_state": self.previous_state,
            "new_state": self.new_state,
            "evidence_id": self.evidence_id,
            "metadata": self.metadata,
        }


class TimelineService:
    """Service for aggregating timeline events from multiple sources."""
    
    @staticmethod
    def get_domain_timeline(domain_id: str, user_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get a comprehensive timeline for a domain.
        
        Aggregates events from:
        - DNS observations
        - DNS record changes
        - IP address observations
        - DNS findings
        - Audit events related to this domain
        - Investigation events
        - Lifecycle assessments
        
        Args:
            domain_id: The ID of the domain
            user_id: The ID of the user (for filtering)
            limit: Maximum number of events to return
            
        Returns:
            List of timeline events sorted by timestamp (newest first)
        """
        events: List[TimelineEvent] = []
        
        # Get DNS observations
        dns_observations = DNSObservation.objects.filter(
            domain_id=domain_id,
            domain__owner_id=user_id
        ).order_by('-observed_at')[:limit]
        
        for obs in dns_observations:
            events.append(TimelineEvent(
                event_id=str(obs.id),
                event_type="DNS_OBSERVATION",
                timestamp=obs.observed_at.isoformat(),
                asset=obs.hostname,
                description=f"DNS {obs.record_type} query: {', '.join(obs.values) if obs.values else 'No answer'}",
                source=obs.source,
                evidence_id=str(obs.id),
                metadata={
                    "record_type": obs.record_type,
                    "values": obs.values,
                    "response_code": obs.response_code,
                    "confidence": obs.confidence,
                }
            ))
        
        # Get DNS record changes (historical vs current)
        dns_records = DNSRecord.objects.filter(
            domain_id=domain_id,
            domain__owner_id=user_id
        ).order_by('-last_seen')[:limit]
        
        for record in dns_records:
            status = "HISTORICAL" if not record.is_current else "CURRENT"
            events.append(TimelineEvent(
                event_id=str(record.id),
                event_type="DNS_RECORD",
                timestamp=record.last_seen.isoformat(),
                asset=record.hostname,
                description=f"DNS {record.record_type} record: {record.value}",
                source="DNS Intelligence",
                new_state=status,
                evidence_id=str(record.id),
                metadata={
                    "record_type": record.record_type,
                    "value": record.value,
                    "is_current": record.is_current,
                    "first_seen": record.first_seen.isoformat(),
                }
            ))
        
        # Get IP address observations
        ip_addresses = IPAddress.objects.filter(
            domain_id=domain_id,
            domain__owner_id=user_id
        ).order_by('-last_seen')[:limit]
        
        for ip in ip_addresses:
            events.append(TimelineEvent(
                event_id=str(ip.id),
                event_type="IP_ADDRESS",
                timestamp=ip.last_seen.isoformat(),
                asset=ip.address,
                description=f"IP {ip.address} ({ip.version}) - {ip.association_status}",
                source="RDAP" if ip.rdap_available else "DNS Resolution",
                new_state=ip.association_status,
                evidence_id=str(ip.id),
                metadata={
                    "version": ip.version,
                    "organization": ip.organization,
                    "country": ip.country,
                    "asn": ip.asn,
                    "is_likely_cdn": ip.is_likely_cdn,
                }
            ))
        
        # Get DNS findings
        dns_findings = DNSFinding.objects.filter(
            domain_id=domain_id,
            domain__owner_id=user_id
        ).order_by('-created_at')[:limit]
        
        for finding in dns_findings:
            events.append(TimelineEvent(
                event_id=str(finding.id),
                event_type="DNS_FINDING",
                timestamp=finding.created_at.isoformat(),
                asset=finding.domain.name,
                description=f"{finding.severity}: {finding.title}",
                source="DNS Analyzer",
                evidence_id=str(finding.id),
                metadata={
                    "severity": finding.severity,
                    "title": finding.title,
                    "description": finding.description,
                    "evidence": finding.evidence,
                }
            ))
        
        # Get audit events related to this domain
        audit_events = AuditEvent.objects.filter(
            Q(resource_id=domain_id) | Q(metadata__domain_id=domain_id),
            actor_id=user_id
        ).order_by('-timestamp')[:limit]
        
        for audit in audit_events:
            events.append(TimelineEvent(
                event_id=str(audit.id),
                event_type="AUDIT_EVENT",
                timestamp=audit.timestamp.isoformat(),
                asset=audit.resource_name or "System",
                description=audit.action,
                source="Audit Log",
                new_state=audit.result,
                metadata={
                    "event_type": audit.event_type,
                    "result": audit.result,
                    "resource_type": audit.resource_type,
                }
            ))
        
        # Get investigation events
        investigations = Investigation.objects.filter(
            domain_id=domain_id,
            owner_id=user_id
        ).order_by('-created_at')[:limit]
        
        for inv in investigations:
            events.append(TimelineEvent(
                event_id=str(inv.id),
                event_type="INVESTIGATION",
                timestamp=inv.created_at.isoformat(),
                asset=inv.domain.name,
                description=f"Investigation '{inv.title}' created",
                source="Investigation System",
                new_state=inv.status,
                evidence_id=str(inv.id),
                metadata={
                    "title": inv.title,
                    "status": inv.status,
                    "priority": inv.priority,
                }
            ))
            
            # Add status change events
            if inv.updated_at != inv.created_at:
                events.append(TimelineEvent(
                    event_id=f"{inv.id}_updated",
                    event_type="INVESTIGATION_STATUS_CHANGE",
                    timestamp=inv.updated_at.isoformat(),
                    asset=inv.domain.name,
                    description=f"Investigation '{inv.title}' status updated to {inv.status}",
                    source="Investigation System",
                    new_state=inv.status,
                    evidence_id=str(inv.id),
                    metadata={
                        "title": inv.title,
                        "status": inv.status,
                    }
                ))
        
        # Get analyst notes
        analyst_notes = AnalystNote.objects.filter(
            investigation__domain_id=domain_id,
            author_id=user_id
        ).order_by('-created_at')[:limit]
        
        for note in analyst_notes:
            events.append(TimelineEvent(
                event_id=str(note.id),
                event_type="ANALYST_NOTE",
                timestamp=note.created_at.isoformat(),
                asset=note.investigation.domain.name,
                description=f"Analyst note: {note.content[:100]}...",
                source="Analyst",
                evidence_id=str(note.id),
                metadata={
                    "investigation_id": str(note.investigation.id),
                    "author": note.author.username,
                }
            ))
        
        # Get lifecycle assessments
        assessments = LifecycleAssessment.objects.filter(
            domain_id=domain_id,
            owner_id=user_id
        ).order_by('-generated_at')[:limit]
        
        for assessment in assessments:
            events.append(TimelineEvent(
                event_id=str(assessment.id),
                event_type="LIFECYCLE_ASSESSMENT",
                timestamp=assessment.generated_at.isoformat(),
                asset=assessment.domain.name,
                description=f"Lifecycle classification: {assessment.classification} (confidence: {assessment.confidence})",
                source="Lifecycle Engine",
                new_state=assessment.classification,
                evidence_id=str(assessment.id),
                metadata={
                    "classification": assessment.classification,
                    "confidence": str(assessment.confidence),
                    "model_version": assessment.model_version,
                    "explanation": assessment.explanation,
                }
            ))
        
        # Sort all events by timestamp (newest first)
        events.sort(key=lambda e: e.timestamp, reverse=True)
        
        # Apply limit
        events = events[:limit]
        
        return [event.to_dict() for event in events]
    
    @staticmethod
    def get_investigation_timeline(investigation_id: str, user_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get a timeline for a specific investigation.
        
        Args:
            investigation_id: The ID of the investigation
            user_id: The ID of the user (for filtering)
            limit: Maximum number of events to return
            
        Returns:
            List of timeline events sorted by timestamp (newest first)
        """
        events: List[TimelineEvent] = []
        
        try:
            investigation = Investigation.objects.get(id=investigation_id, owner_id=user_id)
            domain_id = investigation.domain.id
        except Investigation.DoesNotExist:
            return []
        
        # Get the domain timeline and filter for events relevant to this investigation
        domain_events = TimelineService.get_domain_timeline(domain_id, user_id, limit * 2)
        
        # Add investigation-specific events
        events.append(TimelineEvent(
            event_id=str(investigation.id),
            event_type="INVESTIGATION_CREATED",
            timestamp=investigation.created_at.isoformat(),
            asset=investigation.domain.name,
            description=f"Investigation '{investigation.title}' created",
            source="Investigation System",
            new_state=investigation.status,
            evidence_id=str(investigation.id),
            metadata={
                "title": investigation.title,
                "priority": investigation.priority,
            }
        ).to_dict())
        
        # Add analyst notes for this investigation
        notes = AnalystNote.objects.filter(
            investigation_id=investigation_id,
            author_id=user_id
        ).order_by('-created_at')[:limit]
        
        for note in notes:
            events.append(TimelineEvent(
                event_id=str(note.id),
                event_type="ANALYST_NOTE",
                timestamp=note.created_at.isoformat(),
                asset=investigation.domain.name,
                description=f"Analyst note: {note.content[:100]}...",
                source="Analyst",
                evidence_id=str(note.id),
                metadata={
                    "investigation_id": str(investigation.id),
                    "author": note.author.username,
                }
            ).to_dict())
        
        # Sort by timestamp
        events.sort(key=lambda e: e["timestamp"], reverse=True)
        
        return events[:limit]
    
    @staticmethod
    def get_user_timeline(user_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get a timeline of all events for a user across all their domains.
        
        Args:
            user_id: The ID of the user
            limit: Maximum number of events to return
            
        Returns:
            List of timeline events sorted by timestamp (newest first)
        """
        events: List[TimelineEvent] = []
        
        # Get audit events for the user
        audit_events = AuditEvent.objects.filter(
            actor_id=user_id
        ).order_by('-timestamp')[:limit]
        
        for audit in audit_events:
            events.append(TimelineEvent(
                event_id=str(audit.id),
                event_type="AUDIT_EVENT",
                timestamp=audit.timestamp.isoformat(),
                asset=audit.resource_name or "System",
                description=audit.action,
                source="Audit Log",
                new_state=audit.result,
                metadata={
                    "event_type": audit.event_type,
                    "result": audit.result,
                    "resource_type": audit.resource_type,
                }
            ))
        
        # Sort by timestamp
        events.sort(key=lambda e: e.timestamp, reverse=True)
        
        return [event.to_dict() for event in events[:limit]]
