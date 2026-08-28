from unittest.mock import patch

import pytest

from apps.dns_intelligence.models import Domain, DNSRecord, ScanJob
from apps.infrastructure.models import IPAddress, InfrastructureObservation
from apps.infrastructure.rdap_client import RDAPResult
from apps.infrastructure.tasks import run_infrastructure_analysis, _init_progress


@pytest.fixture
def domain(db, django_user_model):
    user = django_user_model.objects.create_user(username="tester", password="Str0ngPassw0rd!")
    d = Domain.objects.create(owner=user, name="example.com", authorized=True)
    DNSRecord.objects.create(domain=d, hostname="example.com", record_type="A", value="203.0.113.10", is_current=True)
    return d


@pytest.mark.django_db
class TestInfrastructureTask:
    @patch("apps.infrastructure.tasks.dns_resolver.reverse_lookup", return_value="edge.cdnprovider.example")
    @patch("apps.infrastructure.tasks.rdap_client.lookup_ip")
    def test_successful_rdap_populates_ownership_and_cdn_flag(self, mock_rdap, mock_rdns, domain):
        mock_rdap.return_value = RDAPResult(
            address="203.0.113.10", available=True, asn="AS13335",
            network="CLOUDFLARENET", organization="Cloudflare, Inc.", country="US",
        )
        job = ScanJob.objects.create(
            domain=domain, job_type=ScanJob.JobType.INFRASTRUCTURE_ANALYSIS,
            progress_steps=_init_progress(),
        )
        run_infrastructure_analysis(str(job.id))
        job.refresh_from_db()

        assert job.status == ScanJob.Status.COMPLETED
        ip = IPAddress.objects.get(domain=domain, address="203.0.113.10")
        assert ip.rdap_available is True
        assert ip.organization == "Cloudflare, Inc."
        assert ip.is_likely_cdn is True
        assert ip.association_status == IPAddress.AssociationStatus.CURRENT

    @patch("apps.infrastructure.tasks.dns_resolver.reverse_lookup", return_value=None)
    @patch("apps.infrastructure.tasks.rdap_client.lookup_ip")
    def test_failed_rdap_never_fabricates_ownership(self, mock_rdap, mock_rdns, domain):
        """Regression guard for spec Section 43: unavailable providers must
        surface as unavailable, never as invented data."""
        mock_rdap.return_value = RDAPResult(
            address="203.0.113.10", available=False, error="Network error: blocked"
        )
        job = ScanJob.objects.create(
            domain=domain, job_type=ScanJob.JobType.INFRASTRUCTURE_ANALYSIS,
            progress_steps=_init_progress(),
        )
        run_infrastructure_analysis(str(job.id))

        ip = IPAddress.objects.get(domain=domain, address="203.0.113.10")
        assert ip.rdap_available is False
        assert ip.organization is None
        assert ip.asn is None
        assert ip.is_likely_cdn is False

        obs = InfrastructureObservation.objects.get(domain=domain, address="203.0.113.10")
        assert obs.lookup_succeeded is False
        assert obs.confidence == "LOW"

    @patch("apps.infrastructure.tasks.dns_resolver.reverse_lookup", return_value=None)
    @patch("apps.infrastructure.tasks.rdap_client.lookup_ip")
    def test_ip_no_longer_current_marked_historical(self, mock_rdap, mock_rdns, domain):
        mock_rdap.return_value = RDAPResult(address="198.51.100.5", available=False)
        # Pre-existing IP that will no longer appear in current DNS records
        IPAddress.objects.create(
            domain=domain, address="198.51.100.5", version="IPv4",
            association_status=IPAddress.AssociationStatus.CURRENT,
        )
        job = ScanJob.objects.create(
            domain=domain, job_type=ScanJob.JobType.INFRASTRUCTURE_ANALYSIS,
            progress_steps=_init_progress(),
        )
        run_infrastructure_analysis(str(job.id))

        old_ip = IPAddress.objects.get(domain=domain, address="198.51.100.5")
        assert old_ip.association_status == IPAddress.AssociationStatus.HISTORICAL

    def test_no_current_ips_completes_without_error(self, db, django_user_model):
        user = django_user_model.objects.create_user(username="t2", password="Str0ngPassw0rd!")
        d = Domain.objects.create(owner=user, name="noips.example.com", authorized=True)
        job = ScanJob.objects.create(
            domain=d, job_type=ScanJob.JobType.INFRASTRUCTURE_ANALYSIS,
            progress_steps=_init_progress(),
        )
        run_infrastructure_analysis(str(job.id))
        job.refresh_from_db()
        assert job.status == ScanJob.Status.COMPLETED
        assert IPAddress.objects.filter(domain=d).count() == 0
