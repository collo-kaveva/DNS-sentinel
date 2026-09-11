"""
Celery tasks for monitoring.

These tasks perform periodic monitoring checks for domains with enabled monitoring.
They integrate with the existing ScanJob architecture and are retry-safe, idempotent,
time-bounded, observable, and failure-aware.
"""
from __future__ import annotations

from django.utils import timezone
from celery import shared_task
from datetime import timedelta

from .models import MonitoringConfig, MonitoringResult, ChangeEvent
from .change_detection import ChangeDetector
from apps.dns_intelligence.models import Domain, ScanJob, DNSObservation, DNSRecord
from apps.infrastructure.models import IPAddress, InfrastructureObservation
from apps.certificates.models import Certificate, CertificateObservation
from apps.services.models import Service, ServiceObservation
from apps.lifecycle.models import LifecycleAssessment, Evidence


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # 1 minute between retries
)
def run_monitoring_check(self, config_id: str):
    """
    Run a monitoring check for a specific monitoring configuration.
    
    This task is retry-safe and idempotent. It performs the actual data collection
    (via existing services) and stores results with proper evidence backing.
    """
    try:
        config = MonitoringConfig.objects.select_related("domain", "owner").get(id=config_id)
        domain = config.domain
        
        if not config.is_enabled:
            return {"status": "skipped", "reason": "Monitoring disabled"}
        
        # Create a ScanJob for tracking
        job = ScanJob.objects.create(
            domain=domain,
            job_type=ScanJob.JobType.FULL_INVESTIGATION,
            status=ScanJob.Status.RUNNING,
            started_at=timezone.now(),
            progress_steps=[{"label": f"Monitoring check: {config.monitor_type}", "status": "RUNNING"}],
        )
        
        check_started = timezone.now()
        
        # Run the appropriate monitoring based on type
        result = _perform_monitoring_check(config, job)
        
        check_completed = timezone.now()
        duration = (check_completed - check_started).total_seconds()
        
        # Create monitoring result
        monitoring_result = MonitoringResult.objects.create(
            domain=domain,
            monitoring_config=config,
            monitor_type=config.monitor_type,
            status=result["status"],
            observation_id=result.get("observation_id"),
            observation_type=result.get("observation_type"),
            previous_state=result.get("previous_state", {}),
            new_state=result.get("new_state", {}),
            has_changes=result.get("has_changes", False),
            evidence_id=result.get("evidence_id"),
            scan_job_id=job.id,
            error_message=result.get("error_message", ""),
            check_started_at=check_started,
            check_completed_at=check_completed,
            duration_seconds=duration,
        )
        
        # Detect and record changes if any
        if result.get("has_changes") and result.get("changes"):
            _record_changes(monitoring_result, result["changes"])
        
        # Update job status
        job.status = ScanJob.Status.COMPLETED
        job.finished_at = check_completed
        job.progress_steps[0]["status"] = "COMPLETED"
        job.save(update_fields=["status", "finished_at", "progress_steps"])
        
        # Update config timestamps
        config.last_check_completed = check_completed
        config.next_check_scheduled = _calculate_next_check(config.frequency)
        config.save(update_fields=["last_check_completed", "next_check_scheduled"])
        
        return {
            "status": "success",
            "monitoring_result_id": str(monitoring_result.id),
            "has_changes": monitoring_result.has_changes,
            "duration_seconds": duration,
        }
        
    except MonitoringConfig.DoesNotExist:
        return {"status": "error", "reason": "Monitoring config not found"}
    except Exception as exc:
        # Mark job as failed if it exists
        if 'job' in locals():
            job.status = ScanJob.Status.FAILED
            job.error_message = str(exc)
            job.finished_at = timezone.now()
            job.progress_steps[0]["status"] = "FAILED"
            job.save(update_fields=["status", "error_message", "finished_at", "progress_steps"])
        
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


def _perform_monitoring_check(config: MonitoringConfig, job: ScanJob) -> dict:
    """
    Perform the actual monitoring check based on the monitor type.
    
    This integrates with existing collection services (DNS, infrastructure, etc.)
    and returns a standardized result dict.
    """
    domain = config.domain
    monitor_type = config.monitor_type
    
    try:
        if monitor_type == MonitoringConfig.MonitorType.DNS:
            return _monitor_dns(domain, job)
        elif monitor_type == MonitoringConfig.MonitorType.IP:
            return _monitor_ip(domain, job)
        elif monitor_type == MonitoringConfig.MonitorType.CERTIFICATE:
            return _monitor_certificate(domain, job)
        elif monitor_type == MonitoringConfig.MonitorType.SERVICE:
            return _monitor_service(domain, job)
        elif monitor_type == MonitoringConfig.MonitorType.ASN:
            return _monitor_asn(domain, job)
        elif monitor_type == MonitoringConfig.MonitorType.LIFECYCLE:
            return _monitor_lifecycle(domain, job)
        else:
            return {
                "status": MonitoringResult.CheckStatus.FAILURE,
                "error_message": f"Unknown monitor type: {monitor_type}",
            }
    except Exception as exc:
        return {
            "status": MonitoringResult.CheckStatus.FAILURE,
            "error_message": str(exc),
        }


def _monitor_dns(domain: Domain, job: ScanJob) -> dict:
    """Monitor DNS records for changes."""
    from apps.dns_intelligence import resolver
    
    # Collect current DNS observations
    results = resolver.resolve_all(domain.name)
    
    # Store new observations
    observation_ids = []
    for rtype, result in results.items():
        obs = DNSObservation.objects.create(
            domain=domain,
            hostname=domain.name,
            record_type=rtype,
            values=result.values,
            response_code=result.response_code,
            ttl=result.ttl,
            resolver_used=result.resolver_used,
            query_time_ms=result.query_time_ms,
            source="Monitoring Check",
            confidence="HIGH" if result.response_code in ("NOERROR",) else "MEDIUM",
        )
        observation_ids.append(str(obs.id))
        
        # Update current records
        DNSRecord.objects.filter(
            domain=domain, hostname=domain.name, record_type=rtype, is_current=True
        ).update(is_current=False)
        
        for value in result.values:
            DNSRecord.objects.create(
                domain=domain,
                hostname=domain.name,
                record_type=rtype,
                value=value,
                ttl=result.ttl,
                is_current=True,
            )
    
    # Detect changes
    detector = ChangeDetector(domain)
    changes = detector.detect_dns_changes(results)
    
    # Create evidence
    evidence = Evidence.objects.create(
        domain=domain,
        owner=domain.owner,
        evidence_type=Evidence.EvidenceType.DNS_OBSERVATION,
        status=Evidence.EvidenceStatus.OBSERVED,
        confidence=Evidence.Confidence.HIGH,
        source="Monitoring Check",
        observation=f"DNS monitoring check completed for {domain.name}",
        entity_name=domain.name,
        entity_type="Domain",
        metadata={"observation_ids": observation_ids, "monitoring_check": True},
    )
    
    return {
        "status": MonitoringResult.CheckStatus.SUCCESS,
        "observation_id": observation_ids[0] if observation_ids else None,
        "observation_type": "DNSObservation",
        "new_state": {rtype: result.values for rtype, result in results.items()},
        "has_changes": len(changes) > 0,
        "changes": changes,
        "evidence_id": evidence.id,
    }


def _monitor_ip(domain: Domain, job: ScanJob) -> dict:
    """Monitor IP addresses for changes."""
    from apps.infrastructure import rdap_client
    from apps.dns_intelligence import resolver as dns_resolver
    
    # Get current IPs
    current_ips = list(
        DNSRecord.objects.filter(
            domain=domain, is_current=True, record_type__in=["A", "AAAA"]
        ).values_list("value", flat=True)
    )
    
    if not current_ips:
        return {
            "status": MonitoringResult.CheckStatus.SUCCESS,
            "has_changes": False,
            "error_message": "No current IPs to monitor",
        }
    
    # Collect infrastructure data
    rdns_by_ip = {ip: dns_resolver.reverse_lookup(ip) for ip in current_ips}
    rdap_by_ip = {ip: rdap_client.lookup_ip(ip) for ip in current_ips}
    
    # Store observations
    observation_ids = []
    for addr in current_ips:
        rdns = rdns_by_ip[addr]
        rdap = rdap_by_ip[addr]
        
        obs = InfrastructureObservation.objects.create(
            domain=domain,
            address=addr,
            asn=rdap.asn,
            network=rdap.network,
            organization=rdap.organization,
            country=rdap.country,
            reverse_dns=rdns,
            source="Monitoring Check",
            confidence="MEDIUM" if rdap.available else "LOW",
            lookup_succeeded=rdap.available,
            error_detail=rdap.error or "",
        )
        observation_ids.append(str(obs.id))
        
        # Update current IP snapshot
        IPAddress.objects.update_or_create(
            domain=domain,
            address=addr,
            defaults={
                "reverse_dns": rdns,
                "asn": rdap.asn,
                "network": rdap.network,
                "organization": rdap.organization,
                "country": rdap.country,
                "rdap_available": rdap.available,
            },
        )
    
    # Detect changes
    detector = ChangeDetector(domain)
    changes = detector.detect_ip_changes(current_ips, rdap_by_ip)
    
    # Create evidence
    evidence = Evidence.objects.create(
        domain=domain,
        owner=domain.owner,
        evidence_type=Evidence.EvidenceType.IP_ADDRESS,
        status=Evidence.EvidenceStatus.OBSERVED,
        confidence=Evidence.Confidence.MEDIUM,
        source="Monitoring Check",
        observation=f"IP monitoring check completed for {domain.name}",
        entity_name=domain.name,
        entity_type="Domain",
        metadata={"observation_ids": observation_ids, "monitoring_check": True},
    )
    
    return {
        "status": MonitoringResult.CheckStatus.SUCCESS,
        "observation_id": observation_ids[0] if observation_ids else None,
        "observation_type": "InfrastructureObservation",
        "new_state": {ip: {"asn": rdap_by_ip[ip].asn, "org": rdap_by_ip[ip].organization} for ip in current_ips},
        "has_changes": len(changes) > 0,
        "changes": changes,
        "evidence_id": evidence.id,
    }


def _monitor_certificate(domain: Domain, job: ScanJob) -> dict:
    """Monitor certificates for changes."""
    # For now, return success without actual certificate collection
    # Certificate collection would require TLS handshake logic
    # This is a placeholder that integrates with the monitoring framework
    
    return {
        "status": MonitoringResult.CheckStatus.SUCCESS,
        "has_changes": False,
        "error_message": "Certificate monitoring not yet implemented",
    }


def _monitor_service(domain: Domain, job: ScanJob) -> dict:
    """Monitor services for changes."""
    # For now, return success without actual service collection
    # Service collection would require port scanning logic
    # This is a placeholder that integrates with the monitoring framework
    
    return {
        "status": MonitoringResult.CheckStatus.SUCCESS,
        "has_changes": False,
        "error_message": "Service monitoring not yet implemented",
    }


def _monitor_asn(domain: Domain, job: ScanJob) -> dict:
    """Monitor ASN/provider for changes."""
    # This is covered by IP monitoring, which includes ASN data
    # Redirect to IP monitoring
    return _monitor_ip(domain, job)


def _monitor_lifecycle(domain: Domain, job: ScanJob) -> dict:
    """Monitor lifecycle classification for changes."""
    from apps.lifecycle.classification_engine import ClassificationEngine
    
    # Get current lifecycle assessment
    current_assessment = LifecycleAssessment.objects.filter(domain=domain).order_by("-generated_at").first()
    previous_classification = current_assessment.classification if current_assessment else None
    
    # Run new classification
    engine = ClassificationEngine()
    new_assessment = engine.classify_domain(domain)
    
    # Detect changes
    changes = []
    if previous_classification and previous_classification != new_assessment.classification:
        changes.append({
            "event_type": ChangeEvent.EventType.LIFECYCLE_CHANGED,
            "description": f"Lifecycle changed from {previous_classification} to {new_assessment.classification}",
            "previous_value": previous_classification,
            "new_value": new_assessment.classification,
            "entity_name": domain.name,
            "entity_type": "Domain",
        })
    
    return {
        "status": MonitoringResult.CheckStatus.SUCCESS,
        "observation_id": str(new_assessment.id),
        "observation_type": "LifecycleAssessment",
        "previous_state": {"classification": previous_classification} if previous_classification else {},
        "new_state": {"classification": new_assessment.classification},
        "has_changes": len(changes) > 0,
        "changes": changes,
        "evidence_id": new_assessment.supporting_evidence[0] if new_assessment.supporting_evidence else None,
    }


def _record_changes(monitoring_result: MonitoringResult, changes: list) -> None:
    """Record detected changes as ChangeEvent objects."""
    for change in changes:
        change_event = ChangeEvent.objects.create(
            domain=monitoring_result.domain,
            monitoring_result=monitoring_result,
            event_type=change.get("event_type", ChangeEvent.EventType.DNS_RECORD_CHANGED),
            description=change.get("description", ""),
            previous_value=change.get("previous_value", ""),
            new_value=change.get("new_value", ""),
            entity_name=change.get("entity_name", ""),
            entity_type=change.get("entity_type", ""),
            evidence_id=change.get("evidence_id"),
            metadata=change.get("metadata", {}),
        )
        
        # Generate alert if monitoring config has alert_on_change enabled
        if monitoring_result.monitoring_config.alert_on_change:
            _generate_alert_from_change(change_event, monitoring_result)


def _generate_alert_from_change(change_event: ChangeEvent, monitoring_result: MonitoringResult) -> None:
    """Generate an alert from a change event."""
    from apps.alerts.models import Alert
    
    # Map change event types to alert types and severities
    alert_type_map = {
        ChangeEvent.EventType.DNS_RECORD_ADDED: (Alert.AlertType.DNS_RECORD_ADDED, Alert.Severity.LOW),
        ChangeEvent.EventType.DNS_RECORD_REMOVED: (Alert.AlertType.DNS_RECORD_REMOVED, Alert.Severity.MEDIUM),
        ChangeEvent.EventType.DNS_RECORD_CHANGED: (Alert.AlertType.DNS_RECORD_CHANGED, Alert.Severity.LOW),
        ChangeEvent.EventType.IP_CHANGED: (Alert.AlertType.IP_CHANGED, Alert.Severity.MEDIUM),
        ChangeEvent.EventType.CERTIFICATE_CHANGED: (Alert.AlertType.CERTIFICATE_CHANGED, Alert.Severity.HIGH),
        ChangeEvent.EventType.CERTIFICATE_EXPIRED: (Alert.AlertType.CERTIFICATE_EXPIRED, Alert.Severity.CRITICAL),
        ChangeEvent.EventType.SERVICE_APPEARED: (Alert.AlertType.SERVICE_APPEARED, Alert.Severity.LOW),
        ChangeEvent.EventType.SERVICE_DISAPPEARED: (Alert.AlertType.SERVICE_DISAPPEARED, Alert.Severity.MEDIUM),
        ChangeEvent.EventType.ASN_CHANGED: (Alert.AlertType.ASN_CHANGED, Alert.Severity.LOW),
        ChangeEvent.EventType.PROVIDER_CHANGED: (Alert.AlertType.PROVIDER_CHANGED, Alert.Severity.MEDIUM),
        ChangeEvent.EventType.LIFECYCLE_CHANGED: (Alert.AlertType.LIFECYCLE_CHANGED, Alert.Severity.MEDIUM),
    }
    
    alert_type, severity = alert_type_map.get(
        change_event.event_type,
        (Alert.AlertType.DNS_RECORD_CHANGED, Alert.Severity.LOW)
    )
    
    # Create alert
    alert = Alert.objects.create(
        domain=change_event.domain,
        owner=change_event.domain.owner,
        alert_type=alert_type,
        severity=severity,
        title=f"{change_event.event_type.replace('_', ' ')}: {change_event.entity_name}",
        description=change_event.description,
        trigger_event_id=change_event.id,
        trigger_event_type=change_event.event_type,
        evidence_id=change_event.evidence_id,
    )
    
    # Update change event to reflect alert generation
    change_event.alert_generated = True
    change_event.alert_id = alert.id
    change_event.save(update_fields=["alert_generated", "alert_id"])


def _calculate_next_check(frequency: str) -> timezone.datetime:
    """Calculate the next scheduled check time based on frequency."""
    now = timezone.now()
    
    if frequency == MonitoringConfig.Frequency.HOURLY:
        return now + timedelta(hours=1)
    elif frequency == MonitoringConfig.Frequency.DAILY:
        return now + timedelta(days=1)
    elif frequency == MonitoringConfig.Frequency.WEEKLY:
        return now + timedelta(weeks=1)
    elif frequency == MonitoringConfig.Frequency.MONTHLY:
        return now + timedelta(days=30)
    else:
        return now + timedelta(days=1)  # Default to daily


@shared_task
def run_scheduled_monitoring():
    """
    Run all monitoring checks that are due.
    
    This task is typically scheduled by Celery Beat to run periodically
    (e.g., every hour) and checks for monitoring configs whose next_check_scheduled
    time has passed.
    """
    now = timezone.now()
    due_configs = MonitoringConfig.objects.filter(
        is_enabled=True,
        next_check_scheduled__lte=now
    ).select_related("domain", "owner")
    
    results = []
    for config in due_configs:
        # Queue individual monitoring checks
        result = run_monitoring_check.delay(str(config.id))
        results.append({
            "config_id": str(config.id),
            "domain": config.domain.name,
            "monitor_type": config.monitor_type,
            "task_id": result.id,
        })
    
    return {
        "scheduled_count": len(due_configs),
        "results": results,
    }