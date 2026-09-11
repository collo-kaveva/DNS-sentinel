from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from rest_framework import generics, permissions, status, viewsets, filters
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action

from .serializers import RegisterSerializer, UserSerializer, AuditEventSerializer, UserSettingsSerializer
from .models import AuditEvent, UserSettings
from apps.dns_intelligence.models import Domain, DNSFinding
from apps.infrastructure.models import IPAddress
from apps.lifecycle.models import LifecycleAssessment

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {"user": UserSerializer(user).data, "token": token.key},
            status=status.HTTP_201_CREATED,
        )


class LoginView(ObtainAuthToken):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"user": UserSerializer(user).data, "token": token.key})


class LogoutView(APIView):
    def post(self, request):
        request.user.auth_token.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)


class AuditEventViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for AuditEvent model.
    
    Provides read-only access to audit events with filtering capabilities.
    Normal users cannot create, update, or delete audit events.
    """
    serializer_class = AuditEventSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["action", "resource_name", "actor_username"]
    ordering_fields = ["timestamp", "event_type", "result"]
    ordering = ["-timestamp"]
    
    def get_queryset(self):
        """Filter audit events by current user."""
        queryset = AuditEvent.objects.filter(actor=self.request.user)
        
        # Filter by event type if provided
        event_type = self.request.query_params.get("event_type")
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        
        # Filter by resource type if provided
        resource_type = self.request.query_params.get("resource_type")
        if resource_type:
            queryset = queryset.filter(resource_type=resource_type)
        
        # Filter by result if provided
        result = self.request.query_params.get("result")
        if result:
            queryset = queryset.filter(result=result)
        
        # Filter by date range if provided
        date_from = self.request.query_params.get("date_from")
        date_to = self.request.query_params.get("date_to")
        if date_from:
            queryset = queryset.filter(timestamp__gte=date_from)
        if date_to:
            queryset = queryset.filter(timestamp__lte=date_to)
        
        return queryset


class UserSettingsView(generics.RetrieveUpdateAPIView):
    """
    View for retrieving and updating user settings.
    
    Each user has exactly one settings record, created automatically if needed.
    """
    serializer_class = UserSettingsSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        """Get or create settings for the current user."""
        settings, created = UserSettings.objects.get_or_create(
            user=self.request.user
        )
        return settings


class DashboardAPIView(APIView):
    """
    Optimized dashboard API endpoint.
    
    Provides aggregate statistics for the current user's assets, findings,
    lifecycle classifications, and other dashboard metrics in a single
    optimized query to avoid N+1 query problems.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get dashboard statistics for the current user."""
        user = request.user
        
        # Get basic domain counts
        total_domains = Domain.objects.filter(owner=user).count()
        authorized_domains = Domain.objects.filter(owner=user, authorized=True).count()
        
        # Get DNS findings counts by severity
        dns_findings = DNSFinding.objects.filter(domain__owner=user)
        high_severity_count = dns_findings.filter(severity="HIGH").count()
        medium_severity_count = dns_findings.filter(severity="MEDIUM").count()
        low_severity_count = dns_findings.filter(severity="LOW").count()
        info_severity_count = dns_findings.filter(severity="INFO").count()
        
        # Get infrastructure counts
        total_ips = IPAddress.objects.filter(domain__owner=user).count()
        current_ips = IPAddress.objects.filter(
            domain__owner=user, 
            association_status=IPAddress.AssociationStatus.CURRENT
        ).count()
        cdn_ips = IPAddress.objects.filter(domain__owner=user, is_likely_cdn=True).count()
        
        # Get lifecycle classifications
        lifecycle_classifications = LifecycleAssessment.objects.filter(domain__owner=user)
        lifecycle_counts = lifecycle_classifications.values('classification').annotate(
            count=Count('id')
        )
        
        lifecycle_summary = {
            "ACTIVE": 0,
            "LEGACY": 0,
            "POTENTIALLY_ABANDONED": 0,
            "LIKELY_ABANDONED": 0,
            "UNKNOWN": 0,
        }
        
        for item in lifecycle_counts:
            classification = item['classification']
            if classification in lifecycle_summary:
                lifecycle_summary[classification] = item['count']
        
        # Get recent activity counts
        from apps.monitoring.models import ChangeEvent, MonitoringResult
        from apps.alerts.models import Alert
        
        recent_changes = ChangeEvent.objects.filter(
            monitoring_result__monitoring_config__owner=user
        ).count()
        
        recent_alerts = Alert.objects.filter(owner=user).count()
        open_alerts = Alert.objects.filter(owner=user, status=Alert.Status.NEW).count()
        
        return Response({
            "domains": {
                "total": total_domains,
                "authorized": authorized_domains,
                "unauthorized": total_domains - authorized_domains,
            },
            "findings": {
                "high": high_severity_count,
                "medium": medium_severity_count,
                "low": low_severity_count,
                "info": info_severity_count,
                "total": dns_findings.count(),
            },
            "infrastructure": {
                "total_ips": total_ips,
                "current_ips": current_ips,
                "cdn_detected": cdn_ips,
            },
            "lifecycle": lifecycle_summary,
            "monitoring": {
                "recent_changes": recent_changes,
                "total_alerts": recent_alerts,
                "open_alerts": open_alerts,
            },
            "attention_required": high_severity_count > 0,
        })
