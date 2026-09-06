"""
Audit logging service for tracking security-relevant actions.

This service provides helper functions to create audit events for
important application actions such as login, asset creation, investigation starts, etc.
"""
from typing import Optional, Dict, Any
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import AuditEvent

User = get_user_model()


class AuditService:
    """Service for creating audit events."""
    
    @staticmethod
    def log_event(
        actor: User,
        event_type: str,
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        resource_name: Optional[str] = None,
        result: str = AuditEvent.ActionResult.SUCCESS,
        status_code: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditEvent:
        """
        Create an audit event.
        
        Args:
            actor: The user who performed the action
            event_type: The type of event (from AuditEvent.EventType)
            action: Description of the action performed
            resource_type: Type of resource affected (e.g., 'Domain', 'Investigation')
            resource_id: ID of the affected resource
            resource_name: Human-readable name of the resource
            result: Result of the action (SUCCESS, FAILURE, PARTIAL)
            status_code: HTTP status code or similar
            ip_address: IP address of the request
            user_agent: User agent string
            metadata: Additional structured metadata about the event
            
        Returns:
            The created AuditEvent instance
        """
        # Preserve username even if user is deleted later
        actor_username = actor.username if actor else "System"
        
        return AuditEvent.objects.create(
            actor=actor,
            actor_username=actor_username,
            event_type=event_type,
            action=action,
            resource_type=resource_type or "",
            resource_id=resource_id or "",
            resource_name=resource_name or "",
            result=result,
            status_code=status_code,
            ip_address=ip_address,
            user_agent=user_agent or "",
            metadata=metadata or {},
        )
    
    @staticmethod
    def log_login(user: User, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> AuditEvent:
        """Log a user login event."""
        return AuditService.log_event(
            actor=user,
            event_type=AuditEvent.EventType.LOGIN,
            action="User logged in",
            resource_type="User",
            resource_id=str(user.id),
            resource_name=user.username,
            result=AuditEvent.ActionResult.SUCCESS,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    
    @staticmethod
    def log_logout(user: User, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> AuditEvent:
        """Log a user logout event."""
        return AuditService.log_event(
            actor=user,
            event_type=AuditEvent.EventType.LOGOUT,
            action="User logged out",
            resource_type="User",
            resource_id=str(user.id),
            resource_name=user.username,
            result=AuditEvent.ActionResult.SUCCESS,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    
    @staticmethod
    def log_registration(user: User, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> AuditEvent:
        """Log a user registration event."""
        return AuditService.log_event(
            actor=user,
            event_type=AuditEvent.EventType.REGISTRATION,
            action="User account created",
            resource_type="User",
            resource_id=str(user.id),
            resource_name=user.username,
            result=AuditEvent.ActionResult.SUCCESS,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    
    @staticmethod
    def log_domain_created(user: User, domain_id: str, domain_name: str, ip_address: Optional[str] = None) -> AuditEvent:
        """Log a domain creation event."""
        return AuditService.log_event(
            actor=user,
            event_type=AuditEvent.EventType.DOMAIN_CREATED,
            action=f"Domain '{domain_name}' added to investigation",
            resource_type="Domain",
            resource_id=domain_id,
            resource_name=domain_name,
            result=AuditEvent.ActionResult.SUCCESS,
            ip_address=ip_address,
        )
    
    @staticmethod
    def log_domain_deleted(user: User, domain_id: str, domain_name: str, ip_address: Optional[str] = None) -> AuditEvent:
        """Log a domain deletion event."""
        return AuditService.log_event(
            actor=user,
            event_type=AuditEvent.EventType.DOMAIN_DELETED,
            action=f"Domain '{domain_name}' deleted",
            resource_type="Domain",
            resource_id=domain_id,
            resource_name=domain_name,
            result=AuditEvent.ActionResult.SUCCESS,
            ip_address=ip_address,
        )
    
    @staticmethod
    def log_investigation_started(user: User, investigation_id: str, investigation_title: str, ip_address: Optional[str] = None) -> AuditEvent:
        """Log an investigation start event."""
        return AuditService.log_event(
            actor=user,
            event_type=AuditEvent.EventType.INVESTIGATION_STARTED,
            action=f"Investigation '{investigation_title}' started",
            resource_type="Investigation",
            resource_id=investigation_id,
            resource_name=investigation_title,
            result=AuditEvent.ActionResult.SUCCESS,
            ip_address=ip_address,
        )
    
    @staticmethod
    def log_investigation_completed(user: User, investigation_id: str, investigation_title: str, ip_address: Optional[str] = None) -> AuditEvent:
        """Log an investigation completion event."""
        return AuditService.log_event(
            actor=user,
            event_type=AuditEvent.EventType.INVESTIGATION_COMPLETED,
            action=f"Investigation '{investigation_title}' completed",
            resource_type="Investigation",
            resource_id=investigation_id,
            resource_name=investigation_title,
            result=AuditEvent.ActionResult.SUCCESS,
            ip_address=ip_address,
        )
    
    @staticmethod
    def log_investigation_failed(user: User, investigation_id: str, investigation_title: str, error_message: str, ip_address: Optional[str] = None) -> AuditEvent:
        """Log an investigation failure event."""
        return AuditService.log_event(
            actor=user,
            event_type=AuditEvent.EventType.INVESTIGATION_FAILED,
            action=f"Investigation '{investigation_title}' failed",
            resource_type="Investigation",
            resource_id=investigation_id,
            resource_name=investigation_title,
            result=AuditEvent.ActionResult.FAILURE,
            ip_address=ip_address,
            metadata={"error_message": error_message},
        )
    
    @staticmethod
    def log_scan_started(user: User, domain_id: str, domain_name: str, scan_type: str, ip_address: Optional[str] = None) -> AuditEvent:
        """Log a scan start event."""
        return AuditService.log_event(
            actor=user,
            event_type=AuditEvent.EventType.OTHER,
            action=f"{scan_type} scan started for domain '{domain_name}'",
            resource_type="Domain",
            resource_id=domain_id,
            resource_name=domain_name,
            result=AuditEvent.ActionResult.SUCCESS,
            ip_address=ip_address,
            metadata={"scan_type": scan_type},
        )
    
    @staticmethod
    def log_scan_completed(user: User, domain_id: str, domain_name: str, scan_type: str, ip_address: Optional[str] = None) -> AuditEvent:
        """Log a scan completion event."""
        return AuditService.log_event(
            actor=user,
            event_type=AuditEvent.EventType.OTHER,
            action=f"{scan_type} scan completed for domain '{domain_name}'",
            resource_type="Domain",
            resource_id=domain_id,
            resource_name=domain_name,
            result=AuditEvent.ActionResult.SUCCESS,
            ip_address=ip_address,
            metadata={"scan_type": scan_type},
        )
    
    @staticmethod
    def log_settings_updated(user: User, ip_address: Optional[str] = None) -> AuditEvent:
        """Log a settings update event."""
        return AuditService.log_event(
            actor=user,
            event_type=AuditEvent.EventType.SETTINGS_UPDATED,
            action="User settings updated",
            resource_type="UserSettings",
            resource_id=str(user.id),
            resource_name=user.username,
            result=AuditEvent.ActionResult.SUCCESS,
            ip_address=ip_address,
        )
    
    @staticmethod
    def log_analyst_note_created(user: User, investigation_id: str, investigation_title: str, ip_address: Optional[str] = None) -> AuditEvent:
        """Log an analyst note creation event."""
        return AuditService.log_event(
            actor=user,
            event_type=AuditEvent.EventType.ANALYST_NOTE_CREATED,
            action=f"Analyst note added to investigation '{investigation_title}'",
            resource_type="AnalystNote",
            resource_id=investigation_id,
            resource_name=investigation_title,
            result=AuditEvent.ActionResult.SUCCESS,
            ip_address=ip_address,
        )
    
    @staticmethod
    def log_alert_acknowledged(user: User, alert_id: str, ip_address: Optional[str] = None) -> AuditEvent:
        """Log an alert acknowledgment event."""
        return AuditService.log_event(
            actor=user,
            event_type=AuditEvent.EventType.ALERT_ACKNOWLEDGED,
            action=f"Alert '{alert_id}' acknowledged",
            resource_type="Alert",
            resource_id=alert_id,
            result=AuditEvent.ActionResult.SUCCESS,
            ip_address=ip_address,
        )
    
    @staticmethod
    def log_alert_resolved(user: User, alert_id: str, ip_address: Optional[str] = None) -> AuditEvent:
        """Log an alert resolution event."""
        return AuditService.log_event(
            actor=user,
            event_type=AuditEvent.EventType.ALERT_RESOLVED,
            action=f"Alert '{alert_id}' resolved",
            resource_type="Alert",
            resource_id=alert_id,
            result=AuditEvent.ActionResult.SUCCESS,
            ip_address=ip_address,
        )
    
    @staticmethod
    def log_report_generated(user: User, report_id: str, report_title: str, ip_address: Optional[str] = None) -> AuditEvent:
        """Log a report generation event."""
        return AuditService.log_event(
            actor=user,
            event_type=AuditEvent.EventType.REPORT_GENERATED,
            action=f"Report '{report_title}' generated",
            resource_type="Report",
            resource_id=report_id,
            resource_name=report_title,
            result=AuditEvent.ActionResult.SUCCESS,
            ip_address=ip_address,
        )
    
    @staticmethod
    def log_report_exported(user: User, report_id: str, report_title: str, format: str, ip_address: Optional[str] = None) -> AuditEvent:
        """Log a report export event."""
        return AuditService.log_event(
            actor=user,
            event_type=AuditEvent.EventType.REPORT_EXPORTED,
            action=f"Report '{report_title}' exported as {format}",
            resource_type="Report",
            resource_id=report_id,
            resource_name=report_title,
            result=AuditEvent.ActionResult.SUCCESS,
            ip_address=ip_address,
            metadata={"format": format},
        )
