"""
Celery tasks for report generation.

These tasks generate reports from actual stored observations with proper
provenance tracking and security controls. Report generation is handled
via Celery to avoid blocking Django requests.
"""
from __future__ import annotations

from django.utils import timezone
from celery import shared_task
from typing import Dict, List, Any, Optional

from .models import Report, ReportSection, ReportFinding
from apps.dns_intelligence.models import Domain, DNSObservation, DNSRecord, DNSFinding
from apps.infrastructure.models import IPAddress, InfrastructureObservation
from apps.certificates.models import Certificate, CertificateObservation
from apps.services.models import Service, ServiceObservation
from apps.lifecycle.models import LifecycleAssessment, Evidence
from apps.monitoring.models import MonitoringResult, ChangeEvent
from apps.alerts.models import Alert


@shared_task(bind=True, max_retries=2, default_retry_delay=300)
def generate_report(self, report_id: str):
    """
    Generate a report from actual stored observations.
    
    This task collects data from the database based on the report scope,
    organizes it into sections with proper provenance, and ensures security
    by only including data the user is authorized to access.
    """
    try:
        report = Report.objects.select_related("owner").get(id=report_id)
        
        # Update status to generating
        report.status = Report.Status.GENERATING
        report.save(update_fields=["status"])
        
        # Validate that user owns all domains in scope
        domains = _validate_report_scope(report)
        
        # Generate report content
        content = _generate_report_content(report, domains)
        
        # Store content based on format
        if report.format == Report.Format.JSON:
            report.content = content
        elif report.format == Report.Format.HTML:
            report.content_html = _generate_html_report(content, report)
        
        # Update status to completed
        report.status = Report.Status.COMPLETED
        report.generated_at = timezone.now()
        report.save(update_fields=["status", "content", "content_html", "generated_at"])
        
        # Create audit event
        from apps.accounts.services import AuditService
        AuditService.log_report_generated(report.owner, str(report.id), report.title)
        
        return {"status": "success", "report_id": str(report.id)}
        
    except Report.DoesNotExist:
        return {"status": "error", "reason": "Report not found"}
    except Exception as exc:
        # Mark report as failed
        if 'report' in locals():
            report.status = Report.Status.FAILED
            report.error_message = str(exc)
            report.save(update_fields=["status", "error_message"])
        
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=300 * (2 ** self.request.retries))


def _validate_report_scope(report: Report) -> List[Domain]:
    """
    Validate that the user owns all domains in the report scope.
    
    This ensures security by preventing users from accessing data
    they are not authorized to view.
    """
    domain_ids = report.domains
    if not domain_ids:
        # If no domains specified, include all user's domains
        return list(Domain.objects.filter(owner=report.owner))
    
    # Validate ownership
    domains = list(Domain.objects.filter(
        id__in=domain_ids,
        owner=report.owner
    ))
    
    if len(domains) != len(domain_ids):
        raise ValueError("User does not own all domains in report scope")
    
    return domains


def _generate_report_content(report: Report, domains: List[Domain]) -> Dict[str, Any]:
    """
    Generate report content from actual stored observations.
    
    This function collects data from the database based on the requested sections
    and organizes it with proper provenance tracking.
    """
    content = {
        "report_id": str(report.id),
        "title": report.title,
        "scope_description": report.scope_description,
        "generated_at": timezone.now().isoformat(),
        "domains": [{"id": str(d.id), "name": d.name} for d in domains],
        "sections": {},
    }
    
    # Generate requested sections
    requested_sections = report.requested_sections if report.requested_sections else _get_default_sections()
    
    for section_type in requested_sections:
        section_content = _generate_section(section_type, domains, report)
        if section_content:
            content["sections"][section_type] = section_content
            # Create database section record
            _create_report_section(report, section_type, section_content)
    
    return content


def _get_default_sections() -> List[str]:
    """Get default sections for a report."""
    return [
        "EXECUTIVE_SUMMARY",
        "SCOPE",
        "ASSETS",
        "DNS",
        "CERTIFICATES",
        "INFRASTRUCTURE",
        "SERVICES",
        "LIFECYCLE",
        "MONITORING",
        "ALERTS",
        "FINDINGS",
        "LIMITATIONS",
    ]


def _generate_section(section_type: str, domains: List[Domain], report: Report) -> Optional[Dict[str, Any]]:
    """
    Generate a specific report section with proper provenance.
    
    Each section is generated from actual stored observations with
    evidence backing and source attribution.
    """
    if section_type == "EXECUTIVE_SUMMARY":
        return _generate_executive_summary(domains, report)
    elif section_type == "SCOPE":
        return _generate_scope_section(domains, report)
    elif section_type == "ASSETS":
        return _generate_assets_section(domains, report)
    elif section_type == "DNS":
        return _generate_dns_section(domains, report)
    elif section_type == "CERTIFICATES":
        return _generate_certificates_section(domains, report)
    elif section_type == "INFRASTRUCTURE":
        return _generate_infrastructure_section(domains, report)
    elif section_type == "SERVICES":
        return _generate_services_section(domains, report)
    elif section_type == "LIFECYCLE":
        return _generate_lifecycle_section(domains, report)
    elif section_type == "MONITORING":
        return _generate_monitoring_section(domains, report)
    elif section_type == "ALERTS":
        return _generate_alerts_section(domains, report)
    elif section_type == "FINDINGS":
        return _generate_findings_section(domains, report)
    elif section_type == "LIMITATIONS":
        return _generate_limitations_section(domains, report)
    
    return None


def _generate_executive_summary(domains: List[Domain], report: Report) -> Dict[str, Any]:
    """Generate executive summary section."""
    total_domains = len(domains)
    total_observations = 0
    total_alerts = 0
    
    for domain in domains:
        total_observations += DNSObservation.objects.filter(domain=domain).count()
        total_observations += InfrastructureObservation.objects.filter(domain=domain).count()
        total_alerts += Alert.objects.filter(domain=domain).count()
    
    return {
        "title": "Executive Summary",
        "content": f"This report covers {total_domains} domain(s) with {total_observations} total observations and {total_alerts} alert(s).",
        "findings": [
            {
                "title": "Total Domains",
                "value": total_domains,
                "status": "OBSERVED",
            },
            {
                "title": "Total Observations",
                "value": total_observations,
                "status": "OBSERVED",
            },
            {
                "title": "Total Alerts",
                "value": total_alerts,
                "status": "OBSERVED",
            },
        ],
        "provenance": {
            "source": "Database aggregation",
            "confidence": "HIGH",
            "generated_at": timezone.now().isoformat(),
        },
    }


def _generate_scope_section(domains: List[Domain], report: Report) -> Dict[str, Any]:
    """Generate scope section."""
    return {
        "title": "Report Scope",
        "content": f"This report includes analysis of {len(domains)} domain(s) as specified in the report configuration.",
        "domains": [{"id": str(d.id), "name": d.name, "created_at": d.created_at.isoformat()} for d in domains],
        "provenance": {
            "source": "Report configuration",
            "confidence": "HIGH",
        },
    }


def _generate_assets_section(domains: List[Domain], report: Report) -> Dict[str, Any]:
    """Generate assets section."""
    assets = []
    for domain in domains:
        assets.append({
            "id": str(domain.id),
            "name": domain.name,
            "type": "Domain",
            "authorized": domain.authorized,
            "created_at": domain.created_at.isoformat(),
        })
    
    return {
        "title": "Assets",
        "content": f"Analysis of {len(assets)} asset(s).",
        "assets": assets,
        "provenance": {
            "source": "Domain records",
            "confidence": "HIGH",
        },
    }


def _generate_dns_section(domains: List[Domain], report: Report) -> Dict[str, Any]:
    """Generate DNS section with proper provenance."""
    dns_data = []
    for domain in domains:
        current_records = list(DNSRecord.objects.filter(domain=domain, is_current=True))
        recent_observations = list(DNSObservation.objects.filter(domain=domain)[:10])
        findings = list(DNSFinding.objects.filter(domain=domain))
        
        dns_data.append({
            "domain": domain.name,
            "current_records": [
                {
                    "type": r.record_type,
                    "value": r.value,
                    "ttl": r.ttl,
                    "last_seen": r.last_seen.isoformat(),
                }
                for r in current_records
            ],
            "recent_observations_count": len(recent_observations),
            "findings_count": len(findings),
            "findings": [
                {
                    "severity": f.severity,
                    "title": f.title,
                    "description": f.description,
                }
                for f in findings
            ],
        })
    
    return {
        "title": "DNS Configuration",
        "content": f"DNS analysis for {len(domains)} domain(s).",
        "dns_data": dns_data,
        "provenance": {
            "source": "DNSObservation, DNSRecord, DNSFinding",
            "confidence": "HIGH",
        },
    }


def _generate_certificates_section(domains: List[Domain], report: Report) -> Dict[str, Any]:
    """Generate certificates section."""
    cert_data = []
    for domain in domains:
        certificates = list(Certificate.objects.filter(domain=domain))
        
        for cert in certificates:
            cert_data.append({
                "domain": domain.name,
                "subject": cert.subject,
                "issuer": cert.issuer,
                "valid_from": cert.valid_from.isoformat(),
                "valid_until": cert.valid_until.isoformat(),
                "is_expired": cert.is_expired,
                "is_valid": cert.is_valid,
            })
    
    return {
        "title": "Certificates",
        "content": f"Certificate analysis for {len(domains)} domain(s).",
        "certificates": cert_data,
        "provenance": {
            "source": "Certificate records",
            "confidence": "HIGH",
        },
    }


def _generate_infrastructure_section(domains: List[Domain], report: Report) -> Dict[str, Any]:
    """Generate infrastructure section."""
    infra_data = []
    for domain in domains:
        ip_addresses = list(IPAddress.objects.filter(domain=domain))
        
        for ip in ip_addresses:
            infra_data.append({
                "domain": domain.name,
                "address": str(ip.address),
                "version": ip.version,
                "asn": ip.asn,
                "organization": ip.organization,
                "country": ip.country,
                "rdap_available": ip.rdap_available,
            })
    
    return {
        "title": "Infrastructure",
        "content": f"Infrastructure analysis for {len(domains)} domain(s).",
        "infrastructure": infra_data,
        "provenance": {
            "source": "IPAddress records",
            "confidence": "MEDIUM" if any(not ip.rdap_available for ip in [ip for d in domains for ip in IPAddress.objects.filter(domain=d)]) else "HIGH",
        },
    }


def _generate_services_section(domains: List[Domain], report: Report) -> Dict[str, Any]:
    """Generate services section."""
    service_data = []
    for domain in domains:
        services = list(Service.objects.filter(domain=domain))
        
        for service in services:
            service_data.append({
                "domain": domain.name,
                "ip_address": str(service.ip_address),
                "port": service.port,
                "protocol": service.protocol,
                "service_type": service.service_type,
                "is_available": service.is_available,
            })
    
    return {
        "title": "Services",
        "content": f"Service analysis for {len(domains)} domain(s).",
        "services": service_data,
        "provenance": {
            "source": "Service records",
            "confidence": "MEDIUM",
        },
    }


def _generate_lifecycle_section(domains: List[Domain], report: Report) -> Dict[str, Any]:
    """Generate lifecycle section."""
    lifecycle_data = []
    for domain in domains:
        assessments = list(LifecycleAssessment.objects.filter(domain=domain).order_by("-generated_at")[:5])
        
        for assessment in assessments:
            lifecycle_data.append({
                "domain": domain.name,
                "classification": assessment.classification,
                "confidence": float(assessment.confidence),
                "generated_at": assessment.generated_at.isoformat(),
                "model_version": assessment.model_version,
                "limitations": assessment.limitations,
            })
    
    return {
        "title": "Lifecycle Classification",
        "content": f"Lifecycle analysis for {len(domains)} domain(s).",
        "assessments": lifecycle_data,
        "provenance": {
            "source": "LifecycleAssessment records",
            "confidence": "MEDIUM",
        },
    }


def _generate_monitoring_section(domains: List[Domain], report: Report) -> Dict[str, Any]:
    """Generate monitoring section."""
    monitoring_data = []
    for domain in domains:
        results = list(MonitoringResult.objects.filter(domain=domain).order_by("-created_at")[:10])
        changes = list(ChangeEvent.objects.filter(domain=domain).order_by("-detected_at")[:10])
        
        monitoring_data.append({
            "domain": domain.name,
            "recent_checks": len(results),
            "recent_changes": len(changes),
            "changes": [
                {
                    "event_type": c.event_type,
                    "description": c.description,
                    "detected_at": c.detected_at.isoformat(),
                }
                for c in changes
            ],
        })
    
    return {
        "title": "Monitoring",
        "content": f"Monitoring activity for {len(domains)} domain(s).",
        "monitoring_data": monitoring_data,
        "provenance": {
            "source": "MonitoringResult, ChangeEvent records",
            "confidence": "HIGH",
        },
    }


def _generate_alerts_section(domains: List[Domain], report: Report) -> Dict[str, Any]:
    """Generate alerts section."""
    alert_data = []
    for domain in domains:
        alerts = list(Alert.objects.filter(domain=domain).order_by("-created_at")[:20])
        
        for alert in alerts:
            alert_data.append({
                "domain": domain.name,
                "alert_type": alert.alert_type,
                "severity": alert.severity,
                "status": alert.status,
                "title": alert.title,
                "description": alert.description,
                "created_at": alert.created_at.isoformat(),
            })
    
    return {
        "title": "Alerts",
        "content": f"Alert history for {len(domains)} domain(s).",
        "alerts": alert_data,
        "provenance": {
            "source": "Alert records",
            "confidence": "HIGH",
        },
    }


def _generate_findings_section(domains: List[Domain], report: Report) -> Dict[str, Any]:
    """Generate findings section with provenance."""
    findings = []
    
    # Collect DNS findings
    for domain in domains:
        dns_findings = DNSFinding.objects.filter(domain=domain)
        for finding in dns_findings:
            findings.append({
                "domain": domain.name,
                "type": "DNS",
                "severity": finding.severity,
                "title": finding.title,
                "description": finding.description,
                "evidence": finding.evidence,
                "status": "OBSERVED",
                "confidence": "HIGH",
            })
    
    return {
        "title": "Findings",
        "content": f"Analysis findings for {len(domains)} domain(s).",
        "findings": findings,
        "provenance": {
            "source": "DNSFinding records",
            "confidence": "HIGH",
        },
    }


def _generate_limitations_section(domains: List[Domain], report: Report) -> Dict[str, Any]:
    """Generate limitations section."""
    limitations = [
        "This report is based on publicly observable data only.",
        "RDAP data may be unavailable for some IP addresses due to network restrictions.",
        "Certificate monitoring may not include all certificates if not publicly observable.",
        "Service detection is limited to common ports and protocols.",
        "Lifecycle classification is based on heuristics and may not reflect actual operational status.",
        "Findings are based on passive observation and do not include authenticated assessment.",
    ]
    
    return {
        "title": "Limitations",
        "content": "Known limitations and data availability issues.",
        "limitations": limitations,
        "provenance": {
            "source": "Platform documentation",
            "confidence": "HIGH",
        },
    }


def _create_report_section(report: Report, section_type: str, content: Dict[str, Any]) -> None:
    """Create a database record for a report section."""
    # Map section types to enum values
    section_type_map = {
        "EXECUTIVE_SUMMARY": ReportSection.SectionType.EXECUTIVE_SUMMARY,
        "SCOPE": ReportSection.SectionType.SCOPE,
        "ASSETS": ReportSection.SectionType.ASSETS,
        "DNS": ReportSection.SectionType.DNS,
        "CERTIFICATES": ReportSection.SectionType.CERTIFICATES,
        "INFRASTRUCTURE": ReportSection.SectionType.INFRASTRUCTURE,
        "SERVICES": ReportSection.SectionType.SERVICES,
        "LIFECYCLE": ReportSection.SectionType.LIFECYCLE,
        "MONITORING": ReportSection.SectionType.MONITORING,
        "ALERTS": ReportSection.SectionType.ALERTS,
        "FINDINGS": ReportSection.SectionType.FINDINGS,
        "LIMITATIONS": ReportSection.SectionType.LIMITATIONS,
    }
    
    enum_type = section_type_map.get(section_type, ReportSection.SectionType.FINDINGS)
    
    section = ReportSection.objects.create(
        report=report,
        section_type=enum_type,
        title=content.get("title", section_type),
        content=content.get("content", ""),
        findings=content.get("findings", []),
        status=content.get("provenance", {}).get("confidence", "MEDIUM"),
        confidence=content.get("provenance", {}).get("confidence", "MEDIUM"),
        order=len(report.sections.all()),  # Append to end
    )
    
    # Create detailed finding records if present
    for finding in content.get("findings", []):
        if isinstance(finding, dict):
            ReportFinding.objects.create(
                report_section=section,
                title=finding.get("title", ""),
                description=finding.get("description", ""),
                severity=finding.get("severity", "MEDIUM"),
                finding_status=finding.get("status", "OBSERVED"),
            )


def _generate_html_report(content: Dict[str, Any], report: Report) -> str:
    """Generate HTML version of the report."""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{report.title}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            h1 {{ color: #333; }}
            h2 {{ color: #666; margin-top: 30px; }}
            .section {{ margin-bottom: 30px; }}
            .finding {{ padding: 10px; margin: 10px 0; background: #f5f5f5; }}
            .severity-HIGH {{ border-left: 4px solid #d32f2f; }}
            .severity-MEDIUM {{ border-left: 4px solid #f57c00; }}
            .severity-LOW {{ border-left: 4px solid #388e3c; }}
        </style>
    </head>
    <body>
        <h1>{report.title}</h1>
        <p>Generated: {content.get('generated_at', 'N/A')}</p>
        <p>Scope: {content.get('scope_description', 'N/A')}</p>
    """
    
    for section_type, section_content in content.get("sections", {}).items():
        html += f"""
        <div class="section">
            <h2>{section_content.get('title', section_type)}</h2>
            <p>{section_content.get('content', '')}</p>
        """
        
        # Add findings if present
        for finding in section_content.get("findings", []):
            if isinstance(finding, dict):
                severity = finding.get("severity", "LOW")
                html += f"""
                <div class="finding severity-{severity}">
                    <strong>{finding.get('title', 'Finding')}</strong>: {finding.get('value', finding.get('description', ''))}
                </div>
                """
        
        html += "</div>"
    
    html += """
    </body>
    </html>
    """
    
    return html