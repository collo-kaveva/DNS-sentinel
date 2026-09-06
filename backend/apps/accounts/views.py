from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status, viewsets, filters
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action

from .serializers import RegisterSerializer, UserSerializer, AuditEventSerializer, UserSettingsSerializer
from .models import AuditEvent, UserSettings

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
