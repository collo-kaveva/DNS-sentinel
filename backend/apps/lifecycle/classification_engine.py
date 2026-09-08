"""
Lifecycle classification engine (rule-based).

This engine classifies domains into lifecycle stages using deterministic rules:
- ACTIVE
- LEGACY
- POTENTIALLY_ABANDONED
- LIKELY_ABANDONED
- UNKNOWN

The engine is:
- Rule-based (not ML)
- Explainable
- Versioned
- Deterministic
- Evidence-driven

Critical rules:
- Missing information must reduce confidence
- Missing information must NOT automatically increase abandonment score
- A failed DNS query is NOT proof that a domain disappeared
- Explicitly distinguish: NO DATA, NEGATIVE RESULT, UNKNOWN, OBSERVED ABSENCE
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from django.utils import timezone

from .models import LifecycleAssessment, Evidence, EvidenceType, EvidenceStatus, Confidence


class LifecycleClassificationEngine:
    """
    Rule-based lifecycle classification engine.
    
    Version: 1.0
    """
    
    MODEL_VERSION = "1.0"
    
    # Time thresholds for classification rules (in days)
    RECENT_OBSERVATION_THRESHOLD = 30
    STALE_OBSERVATION_THRESHOLD = 90
    ABANDONMENT_THRESHOLD = 180
    
    # Confidence thresholds
    HIGH_CONFIDENCE_THRESHOLD = 0.75
    MEDIUM_CONFIDENCE_THRESHOLD = 0.50
    
    @staticmethod
    def classify_domain(domain) -> Dict[str, Any]:
        """
        Classify a domain's lifecycle stage using rule-based analysis.
        
        Args:
            domain: The Domain model instance
            
        Returns:
            Dictionary containing classification results with:
            - classification
            - confidence
            - supporting_evidence (list of evidence IDs)
            - contradicting_evidence (list of evidence IDs)
            - limitations
            - explanation
            - model_version
        """
        # Gather evidence from all sources
        evidence_data = LifecycleClassificationEngine._gather_evidence(domain)
        
        # Apply classification rules
        classification_result = LifecycleClassificationEngine._apply_rules(evidence_data)
        
        # Generate explanation
        explanation = LifecycleClassificationEngine._generate_explanation(
            classification_result,
            evidence_data
        )
        
        # Identify limitations
        limitations = LifecycleClassificationEngine._identify_limitations(evidence_data)
        
        return {
            "classification": classification_result["classification"],
            "confidence": classification_result["confidence"],
            "supporting_evidence": classification_result["supporting_evidence"],
            "contradicting_evidence": classification_result["contradicting_evidence"],
            "limitations": limitations,
            "explanation": explanation,
            "model_version": LifecycleClassificationEngine.MODEL_VERSION,
        }
    
    @staticmethod
    def _gather_evidence(domain) -> Dict[str, Any]:
        """
        Gather evidence from all observation sources for a domain.
        
        Returns:
            Dictionary containing evidence from DNS, certificates, services, etc.
        """
        now = timezone.now()
        
        # Get DNS evidence
        dns_observations = Evidence.objects.filter(
            domain=domain,
            evidence_type__in=[EvidenceType.DNS_OBSERVATION, EvidenceType.DNS_RECORD]
        ).order_by("-observed_at")
        
        # Get certificate evidence
        certificate_evidence = Evidence.objects.filter(
            domain=domain,
            evidence_type=EvidenceType.CERTIFICATE
        ).order_by("-observed_at")
        
        # Get service evidence
        service_evidence = Evidence.objects.filter(
            domain=domain,
            evidence_type=EvidenceType.SERVICE
        ).order_by("-observed_at")
        
        # Get IP evidence
        ip_evidence = Evidence.objects.filter(
            domain=domain,
            evidence_type=EvidenceType.IP_ADDRESS
        ).order_by("-observed_at")
        
        # Calculate recency of observations
        dns_recency = LifecycleClassificationEngine._calculate_recency(dns_observations, now)
        cert_recency = LifecycleClassificationEngine._calculate_recency(certificate_evidence, now)
        service_recency = LifecycleClassificationEngine._calculate_recency(service_evidence, now)
        
        # Check for certificate expiration
        cert_expiration = LifecycleClassificationEngine._check_certificate_expiration(certificate_evidence, now)
        
        # Check for service availability
        service_availability = LifecycleClassificationEngine._check_service_availability(service_evidence)
        
        return {
            "dns_observations": list(dns_observations.values_list("id", flat=True)),
            "certificate_evidence": list(certificate_evidence.values_list("id", flat=True)),
            "service_evidence": list(service_evidence.values_list("id", flat=True)),
            "ip_evidence": list(ip_evidence.values_list("id", flat=True)),
            "dns_recency_days": dns_recency,
            "cert_recency_days": cert_recency,
            "service_recency_days": service_recency,
            "cert_expired": cert_expiration["is_expired"],
            "cert_days_until_expiry": cert_expiration["days_until_expiry"],
            "services_available": service_availability["available_count"],
            "services_total": service_availability["total_count"],
            "has_dns_data": dns_observations.exists(),
            "has_certificate_data": certificate_evidence.exists(),
            "has_service_data": service_evidence.exists(),
            "has_ip_data": ip_evidence.exists(),
        }
    
    @staticmethod
    def _calculate_recency(evidence_queryset, now: datetime) -> Optional[int]:
        """Calculate days since most recent observation."""
        latest = evidence_queryset.first()
        if latest and latest.observed_at:
            delta = now - latest.observed_at
            return delta.days
        return None
    
    @staticmethod
    def _check_certificate_expiration(certificate_evidence, now: datetime) -> Dict[str, Any]:
        """Check certificate expiration status."""
        latest = certificate_evidence.first()
        if not latest or not latest.metadata:
            return {"is_expired": None, "days_until_expiry": None}
        
        valid_until = latest.metadata.get("valid_until")
        if valid_until:
            if isinstance(valid_until, str):
                valid_until = datetime.fromisoformat(valid_until)
            
            if valid_until < now:
                return {"is_expired": True, "days_until_expiry": -1}
            else:
                delta = valid_until - now
                return {"is_expired": False, "days_until_expiry": delta.days}
        
        return {"is_expired": None, "days_until_expiry": None}
    
    @staticmethod
    def _check_service_availability(service_evidence) -> Dict[str, Any]:
        """Check service availability."""
        total = service_evidence.count()
        if total == 0:
            return {"available_count": 0, "total_count": 0}
        
        available = service_evidence.filter(
            metadata__is_available=True
        ).count()
        
        return {"available_count": available, "total_count": total}
    
    @staticmethod
    def _apply_rules(evidence_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply rule-based classification logic.
        
        Returns:
            Dictionary with classification, confidence, and evidence lists.
        """
        supporting_evidence = []
        contradicting_evidence = []
        confidence = 0.0
        classification = LifecycleAssessment.LifecycleStatus.UNKNOWN
        
        dns_recency = evidence_data["dns_recency_days"]
        cert_recency = evidence_data["cert_recency_days"]
        service_recency = evidence_data["service_recency_days"]
        cert_expired = evidence_data["cert_expired"]
        cert_days_until_expiry = evidence_data["cert_days_until_expiry"]
        services_available = evidence_data["services_available"]
        services_total = evidence_data["services_total"]
        
        # Rule 1: ACTIVE - Recent DNS activity + valid certificate + available services
        if (
            dns_recency is not None and dns_recency <= LifecycleClassificationEngine.RECENT_OBSERVATION_THRESHOLD
            and cert_expired is False
            and services_total > 0 and services_available > 0
        ):
            classification = LifecycleAssessment.LifecycleStatus.ACTIVE
            confidence = 0.85
            supporting_evidence.extend(evidence_data["dns_observations"])
            supporting_evidence.extend(evidence_data["certificate_evidence"])
            supporting_evidence.extend(evidence_data["service_evidence"])
        
        # Rule 2: LEGACY - Old DNS activity but still responding, old certificate
        elif (
            dns_recency is not None
            and dns_recency > LifecycleClassificationEngine.RECENT_OBSERVATION_THRESHOLD
            and dns_recency <= LifecycleClassificationEngine.STALE_OBSERVATION_THRESHOLD
            and cert_expired is False
            and cert_days_until_expiry is not None
            and cert_days_until_expiry < LifecycleClassificationEngine.RECENT_OBSERVATION_THRESHOLD
        ):
            classification = LifecycleAssessment.LifecycleStatus.LEGACY
            confidence = 0.70
            supporting_evidence.extend(evidence_data["dns_observations"])
            supporting_evidence.extend(evidence_data["certificate_evidence"])
        
        # Rule 3: POTENTIALLY_ABANDONED - Stale observations, expired certificate, services down
        elif (
            dns_recency is not None
            and dns_recency > LifecycleClassificationEngine.STALE_OBSERVATION_THRESHOLD
            and dns_recency <= LifecycleClassificationEngine.ABANDONMENT_THRESHOLD
        ):
            classification = LifecycleAssessment.LifecycleStatus.POTENTIALLY_ABANDONED
            confidence = 0.60
            supporting_evidence.extend(evidence_data["dns_observations"])
            
            # Add certificate evidence if expired
            if cert_expired:
                supporting_evidence.extend(evidence_data["certificate_evidence"])
            
            # Add service evidence if unavailable
            if services_total > 0 and services_available == 0:
                supporting_evidence.extend(evidence_data["service_evidence"])
        
        # Rule 4: LIKELY_ABANDONED - Very stale observations, no recent activity
        elif (
            dns_recency is not None
            and dns_recency > LifecycleClassificationEngine.ABANDONMENT_THRESHOLD
        ):
            classification = LifecycleAssessment.LifecycleStatus.LIKELY_ABANDONED
            confidence = 0.75
            supporting_evidence.extend(evidence_data["dns_observations"])
        
        # Rule 5: UNKNOWN - Insufficient data
        else:
            classification = LifecycleAssessment.LifecycleStatus.UNKNOWN
            confidence = 0.30
            # No supporting evidence - insufficient data
        
        # Reduce confidence based on missing data
        if not evidence_data["has_dns_data"]:
            confidence *= 0.7
        if not evidence_data["has_certificate_data"]:
            confidence *= 0.9
        if not evidence_data["has_service_data"]:
            confidence *= 0.9
        
        # Ensure confidence is within valid range
        confidence = max(0.0, min(1.0, confidence))
        
        return {
            "classification": classification,
            "confidence": confidence,
            "supporting_evidence": supporting_evidence,
            "contradicting_evidence": contradicting_evidence,
        }
    
    @staticmethod
    def _generate_explanation(classification_result: Dict[str, Any], evidence_data: Dict[str, Any]) -> str:
        """Generate human-readable explanation for the classification."""
        classification = classification_result["classification"]
        confidence = classification_result["confidence"]
        
        dns_recency = evidence_data["dns_recency_days"]
        cert_expired = evidence_data["cert_expired"]
        services_available = evidence_data["services_available"]
        services_total = evidence_data["services_total"]
        
        explanation_parts = []
        
        if classification == LifecycleAssessment.LifecycleStatus.ACTIVE:
            explanation_parts.append("Domain shows recent DNS activity")
            if cert_expired is False:
                explanation_parts.append("Certificate is valid")
            if services_total > 0 and services_available > 0:
                explanation_parts.append(f"{services_available}/{services_total} services are available")
        
        elif classification == LifecycleAssessment.LifecycleStatus.LEGACY:
            explanation_parts.append("Domain shows stale but recent DNS activity")
            if cert_expired is False:
                explanation_parts.append("Certificate is valid but expiring soon")
            explanation_parts.append("Domain may be in maintenance or legacy mode")
        
        elif classification == LifecycleAssessment.LifecycleStatus.POTENTIALLY_ABANDONED:
            explanation_parts.append("Domain shows stale DNS observations")
            if cert_expired:
                explanation_parts.append("Certificate has expired")
            if services_total > 0 and services_available == 0:
                explanation_parts.append("Services are unavailable")
            explanation_parts.append("Domain may be abandoned but requires confirmation")
        
        elif classification == LifecycleAssessment.LifecycleStatus.LIKELY_ABANDONED:
            explanation_parts.append("Domain shows very stale DNS observations")
            explanation_parts.append("No recent activity detected")
            explanation_parts.append("Domain is likely abandoned")
        
        elif classification == LifecycleAssessment.LifecycleStatus.UNKNOWN:
            explanation_parts.append("Insufficient data to classify")
            if not evidence_data["has_dns_data"]:
                explanation_parts.append("No DNS observations available")
            if not evidence_data["has_certificate_data"]:
                explanation_parts.append("No certificate data available")
            if not evidence_data["has_service_data"]:
                explanation_parts.append("No service data available")
        
        # Add confidence level
        confidence_level = "HIGH" if confidence >= LifecycleClassificationEngine.HIGH_CONFIDENCE_THRESHOLD else \
                          "MEDIUM" if confidence >= LifecycleClassificationEngine.MEDIUM_CONFIDENCE_THRESHOLD else "LOW"
        explanation_parts.append(f"Confidence: {confidence_level} ({confidence:.2f})")
        
        return ". ".join(explanation_parts) + "."
    
    @staticmethod
    def _identify_limitations(evidence_data: Dict[str, Any]) -> str:
        """Identify limitations in the classification."""
        limitations = []
        
        if not evidence_data["has_dns_data"]:
            limitations.append("No DNS observations available")
        if not evidence_data["has_certificate_data"]:
            limitations.append("No certificate data available")
        if not evidence_data["has_service_data"]:
            limitations.append("No service data available")
        if not evidence_data["has_ip_data"]:
            limitations.append("No IP address data available")
        
        if evidence_data["dns_recency_days"] is None:
            limitations.append("Cannot determine DNS recency")
        if evidence_data["cert_recency_days"] is None:
            limitations.append("Cannot determine certificate recency")
        
        if not limitations:
            return "No significant limitations"
        
        return "; ".join(limitations) + "."
    
    @staticmethod
    def save_lifecycle_assessment(domain, classification_result: Dict[str, Any]) -> LifecycleAssessment:
        """
        Save a lifecycle assessment to the database.
        
        Args:
            domain: The Domain model instance
            classification_result: Result from classify_domain
            
        Returns:
            LifecycleAssessment instance
        """
        assessment = LifecycleAssessment.objects.create(
            domain=domain,
            owner=domain.owner,
            classification=classification_result["classification"],
            confidence=classification_result["confidence"],
            supporting_evidence=classification_result["supporting_evidence"],
            contradicting_evidence=classification_result["contradicting_evidence"],
            model_version=classification_result["model_version"],
            limitations=classification_result["limitations"],
            explanation=classification_result["explanation"],
        )
        
        return assessment
