from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from .models import Domain, ScanJob, DNSRecord, DNSObservation, DNSFinding
from .serializers import (
    DomainSerializer, ScanJobSerializer, DNSRecordSerializer,
    DNSObservationSerializer, DNSFindingSerializer,
)
from .tasks import run_dns_discovery_and_analysis, _init_progress as _init_dns_progress


class ScanThrottle(UserRateThrottle):
    scope = "scan"


class DomainViewSet(viewsets.ModelViewSet):
    """
    Authorized domains belonging to the current user.

    /api/domains/                 list / create
    /api/domains/{id}/            retrieve / update / delete
    /api/domains/{id}/dns/        current DNS records
    /api/domains/{id}/observations/  raw historical DNS observations
    /api/domains/{id}/findings/   DNS analyzer findings
    /api/domains/{id}/investigate/  kick off DNS discovery + analysis job
    /api/domains/{id}/jobs/       list jobs for this domain
    """

    serializer_class = DomainSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["authorized"]
    search_fields = ["name"]
    ordering_fields = ["created_at", "name"]

    def get_queryset(self):
        return Domain.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=["get"], url_path="dns")
    def dns_records(self, request, pk=None):
        domain = self.get_object()
        qs = DNSRecord.objects.filter(domain=domain, is_current=True)
        return Response(DNSRecordSerializer(qs, many=True).data)

    @action(detail=True, methods=["get"], url_path="observations")
    def observations(self, request, pk=None):
        domain = self.get_object()
        qs = DNSObservation.objects.filter(domain=domain)[:200]
        return Response(DNSObservationSerializer(qs, many=True).data)

    @action(detail=True, methods=["get"], url_path="findings")
    def findings(self, request, pk=None):
        domain = self.get_object()
        qs = DNSFinding.objects.filter(domain=domain)
        return Response(DNSFindingSerializer(qs, many=True).data)

    @action(detail=True, methods=["get"], url_path="jobs")
    def jobs(self, request, pk=None):
        domain = self.get_object()
        qs = ScanJob.objects.filter(domain=domain)
        return Response(ScanJobSerializer(qs, many=True).data)

    @action(
        detail=True, methods=["post"], url_path="investigate",
        throttle_classes=[ScanThrottle],
    )
    def investigate(self, request, pk=None):
        domain = self.get_object()
        if not domain.authorized:
            return Response(
                {"detail": "This domain is not marked as authorized for investigation."},
                status=status.HTTP_403_FORBIDDEN,
            )
        job = ScanJob.objects.create(
            domain=domain,
            job_type=ScanJob.JobType.DNS_DISCOVERY,
            progress_steps=_init_dns_progress(),
        )
        run_dns_discovery_and_analysis.delay(str(job.id))
        return Response(ScanJobSerializer(job).data, status=status.HTTP_202_ACCEPTED)

    @action(
        detail=True, methods=["post"], url_path="investigate-infrastructure",
        throttle_classes=[ScanThrottle],
    )
    def investigate_infrastructure(self, request, pk=None):
        from apps.infrastructure.tasks import run_infrastructure_analysis, _init_progress as _init_infra_progress

        domain = self.get_object()
        if not domain.authorized:
            return Response(
                {"detail": "This domain is not marked as authorized for investigation."},
                status=status.HTTP_403_FORBIDDEN,
            )
        job = ScanJob.objects.create(
            domain=domain,
            job_type=ScanJob.JobType.INFRASTRUCTURE_ANALYSIS,
            progress_steps=_init_infra_progress(),
        )
        run_infrastructure_analysis.delay(str(job.id))
        return Response(ScanJobSerializer(job).data, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=["get"], url_path="infrastructure")
    def infrastructure(self, request, pk=None):
        from apps.infrastructure.models import IPAddress
        from apps.infrastructure.serializers import IPAddressSerializer

        domain = self.get_object()
        qs = IPAddress.objects.filter(domain=domain)
        return Response(IPAddressSerializer(qs, many=True).data)


class ScanJobViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ScanJobSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ScanJob.objects.filter(domain__owner=self.request.user)
