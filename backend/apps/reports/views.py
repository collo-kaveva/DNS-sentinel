"""
Views for the reports app.
"""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Report, ReportSection, ReportFinding
from .serializers import ReportSerializer, ReportCreateSerializer, ReportSectionSerializer, ReportFindingSerializer
from .tasks import generate_report


class ReportViewSet(viewsets.ModelViewSet):
    """
    Report management endpoints.
    
    /api/reports/                 list / create
    /api/reports/{id}/            retrieve / update / delete
    /api/reports/{id}/sections/   report sections
    /api/reports/{id}/download/   download report
    /api/reports/{id}/regenerate/ regenerate report
    """
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["status", "format"]
    search_fields = ["title"]
    ordering_fields = ["created_at", "generated_at", "title"]
    
    def get_queryset(self):
        return Report.objects.filter(owner=self.request.user).select_related("owner")
    
    def get_serializer_class(self):
        if self.action == "create":
            return ReportCreateSerializer
        return ReportSerializer
    
    def perform_create(self, serializer):
        report = serializer.save(owner=self.request.user, status=Report.Status.QUEUED)
        # Queue report generation via Celery
        task = generate_report.delay(str(report.id))
        report.celery_task_id = task.id
        report.save(update_fields=["celery_task_id"])
        return report
    
    @action(detail=True, methods=["get"])
    def sections(self, request, pk=None):
        """Get sections for this report."""
        report = self.get_object()
        qs = ReportSection.objects.filter(report=report).order_by("order")
        return Response(ReportSectionSerializer(qs, many=True).data)
    
    @action(detail=True, methods=["get"])
    def download(self, request, pk=None):
        """Download the report in the specified format."""
        report = self.get_object()
        
        if report.status != Report.Status.COMPLETED:
            return Response(
                {"detail": "Report is not ready for download"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if report.format == Report.Format.JSON:
            return Response(report.content)
        elif report.format == Report.Format.HTML:
            return Response({"content": report.content_html}, headers={"Content-Type": "text/html"})
        elif report.format == Report.Format.PDF:
            return Response(
                {"detail": "PDF download not yet implemented"},
                status=status.HTTP_501_NOT_IMPLEMENTED
            )
        
        return Response(
            {"detail": "Unknown format"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=["post"])
    def regenerate(self, request, pk=None):
        """Regenerate the report."""
        report = self.get_object()
        
        # Update status and queue regeneration
        report.status = Report.Status.QUEUED
        report.error_message = ""
        report.content = {}
        report.content_html = ""
        report.generated_at = None
        report.save(update_fields=["status", "error_message", "content", "content_html", "generated_at"])
        
        # Queue report generation via Celery
        task = generate_report.delay(str(report.id))
        report.celery_task_id = task.id
        report.save(update_fields=["celery_task_id"])
        
        return Response(ReportSerializer(report).data)


class ReportSectionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Report section endpoints.
    
    /api/reports/sections/         list
    /api/reports/sections/{id}/    retrieve
    /api/reports/sections/{id}/findings/  section findings
    """
    serializer_class = ReportSectionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["section_type", "status"]
    ordering_fields = ["order", "created_at"]
    
    def get_queryset(self):
        return ReportSection.objects.filter(
            report__owner=self.request.user
        ).select_related("report")
    
    @action(detail=True, methods=["get"])
    def findings(self, request, pk=None):
        """Get detailed findings for this section."""
        section = self.get_object()
        qs = ReportFinding.objects.filter(report_section=section)
        return Response(ReportFindingSerializer(qs, many=True).data)