from __future__ import annotations

import ipaddress as ip_module

from django.utils import timezone
from celery import shared_task

from apps.dns_intelligence.models import Domain, ScanJob, DNSRecord
from apps.dns_intelligence import resolver as dns_resolver

from . import rdap_client, analyzer
from .models import IPAddress, InfrastructureObservation

STEPS = ["Collect current IPs", "Reverse DNS", "RDAP / ASN lookup", "CDN & hosting heuristics"]


def _init_progress():
    return [{"label": s, "status": "PENDING"} for s in STEPS]


def _mark_step(job: ScanJob, label: str, status: str):
    for step in job.progress_steps:
        if step["label"] == label:
            step["status"] = status
    job.save(update_fields=["progress_steps"])


@shared_task
def run_infrastructure_analysis(job_id: str):
    job = ScanJob.objects.select_related("domain").get(id=job_id)
    domain: Domain = job.domain

    job.status = ScanJob.Status.RUNNING
    job.started_at = timezone.now()
    job.progress_steps = _init_progress()
    job.save(update_fields=["status", "started_at", "progress_steps"])

    try:
        _mark_step(job, "Collect current IPs", "RUNNING")
        current_ips = list(
            DNSRecord.objects.filter(
                domain=domain, is_current=True, record_type__in=["A", "AAAA"]
            ).values_list("value", flat=True)
        )
        _mark_step(job, "Collect current IPs", "COMPLETED")

        if not current_ips:
            job.status = ScanJob.Status.COMPLETED
            job.finished_at = timezone.now()
            job.save(update_fields=["status", "finished_at"])
            return

        _mark_step(job, "Reverse DNS", "RUNNING")
        rdns_by_ip = {ip: dns_resolver.reverse_lookup(ip) for ip in current_ips}
        _mark_step(job, "Reverse DNS", "COMPLETED")

        _mark_step(job, "RDAP / ASN lookup", "RUNNING")
        rdap_by_ip = {ip: rdap_client.lookup_ip(ip) for ip in current_ips}
        _mark_step(job, "RDAP / ASN lookup", "COMPLETED")

        _mark_step(job, "CDN & hosting heuristics", "RUNNING")

        # Mark any previously-current IPs no longer observed as historical
        IPAddress.objects.filter(
            domain=domain, association_status=IPAddress.AssociationStatus.CURRENT
        ).exclude(address__in=current_ips).update(
            association_status=IPAddress.AssociationStatus.HISTORICAL
        )

        for addr in current_ips:
            rdns = rdns_by_ip[addr]
            rdap = rdap_by_ip[addr]

            InfrastructureObservation.objects.create(
                domain=domain,
                address=addr,
                asn=rdap.asn,
                network=rdap.network,
                organization=rdap.organization,
                country=rdap.country,
                reverse_dns=rdns,
                source="RDAP" if rdap.available else "RDAP (unavailable)",
                confidence="MEDIUM" if rdap.available else "LOW",
                lookup_succeeded=rdap.available,
                error_detail=rdap.error or "",
            )

            heuristics = analyzer.classify_ip(rdap.organization, rdns)
            version = "IPv6" if ip_module.ip_address(addr).version == 6 else "IPv4"

            IPAddress.objects.update_or_create(
                domain=domain,
                address=addr,
                defaults={
                    "version": version,
                    "association_status": IPAddress.AssociationStatus.CURRENT,
                    "reverse_dns": rdns,
                    "asn": rdap.asn,
                    "network": rdap.network,
                    "organization": rdap.organization,
                    "country": rdap.country,
                    "rdap_available": rdap.available,
                    **heuristics,
                },
            )

        _mark_step(job, "CDN & hosting heuristics", "COMPLETED")

        job.status = ScanJob.Status.COMPLETED
        job.finished_at = timezone.now()
        job.save(update_fields=["status", "finished_at"])

    except Exception as exc:  # noqa: BLE001
        job.status = ScanJob.Status.FAILED
        job.error_message = str(exc)
        job.finished_at = timezone.now()
        job.save(update_fields=["status", "error_message", "finished_at"])
        raise
