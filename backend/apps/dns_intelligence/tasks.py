from __future__ import annotations

from django.utils import timezone
from celery import shared_task

from . import resolver, analyzer
from .models import Domain, ScanJob, DNSRecord, DNSObservation, DNSFinding

STEPS = [
    "DNS discovery",
    "DNS analysis",
]


def _init_progress():
    return [{"label": s, "status": "PENDING"} for s in STEPS]


def _mark_step(job: ScanJob, label: str, status: str):
    for step in job.progress_steps:
        if step["label"] == label:
            step["status"] = status
    job.save(update_fields=["progress_steps"])


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def run_dns_discovery_and_analysis(self, job_id: str):
    job = ScanJob.objects.select_related("domain").get(id=job_id)
    domain = job.domain

    job.status = ScanJob.Status.RUNNING
    job.started_at = timezone.now()
    job.progress_steps = _init_progress()
    job.save(update_fields=["status", "started_at", "progress_steps"])

    try:
        _mark_step(job, "DNS discovery", "RUNNING")
        results = resolver.resolve_all(domain.name)

        for rtype, result in results.items():
            DNSObservation.objects.create(
                domain=domain,
                hostname=domain.name,
                record_type=rtype,
                values=result.values,
                response_code=result.response_code,
                ttl=result.ttl,
                resolver_used=result.resolver_used,
                query_time_ms=result.query_time_ms,
                source="Public DNS",
                confidence="HIGH" if result.response_code in ("NOERROR",) else "MEDIUM",
            )

            # Update "current" record snapshot (mark old as not current, upsert new)
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

        dnssec_signed = resolver.check_dnssec(domain.name)
        DNSObservation.objects.filter(
            domain=domain, hostname=domain.name, record_type__in=["DNSKEY", "DS"]
        ).update(dnssec_signed=dnssec_signed)

        _mark_step(job, "DNS discovery", "COMPLETED")

        _mark_step(job, "DNS analysis", "RUNNING")
        findings = analyzer.analyze_records(results)
        DNSFinding.objects.filter(domain=domain).delete()
        for f in findings:
            DNSFinding.objects.create(domain=domain, **f)
        _mark_step(job, "DNS analysis", "COMPLETED")

        job.status = ScanJob.Status.COMPLETED
        job.finished_at = timezone.now()
        job.save(update_fields=["status", "finished_at"])

    except Exception as exc:  # noqa: BLE001
        job.status = ScanJob.Status.FAILED
        job.error_message = str(exc)
        job.finished_at = timezone.now()
        job.save(update_fields=["status", "error_message", "finished_at"])
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
