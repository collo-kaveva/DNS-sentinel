"""
Tests for lifecycle app - Evidence, EvidenceRelationship, and LifecycleAssessment.
"""
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from apps.dns_intelligence.models import Domain
from .models import Evidence, EvidenceRelationship, LifecycleAssessment, EvidenceType, EvidenceStatus, Confidence
from .classification_engine import LifecycleClassificationEngine

User = get_user_model()


class EvidenceModelTests(TestCase):
    """Tests for Evidence model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.domain = Domain.objects.create(
            name="example.com",
            owner=self.user
        )
    
    def test_create_evidence(self):
        """Test creating evidence."""
        evidence = Evidence.objects.create(
            domain=self.domain,
            owner=self.user,
            evidence_type=EvidenceType.DNS_OBSERVATION,
            status=EvidenceStatus.OBSERVED,
            confidence=Confidence.HIGH,
            source="DNS Query",
            collection_method="Passive",
            observation="A record found",
            entity_name="example.com",
            entity_type="Domain",
        )
        self.assertEqual(evidence.evidence_type, EvidenceType.DNS_OBSERVATION)
        self.assertEqual(evidence.status, EvidenceStatus.OBSERVED)
        self.assertEqual(evidence.confidence, Confidence.HIGH)
        self.assertIsNotNone(evidence.observed_at)
    
    def test_evidence_status_choices(self):
        """Test evidence status choices."""
        self.assertEqual(EvidenceStatus.OBSERVED, "OBSERVED")
        self.assertEqual(EvidenceStatus.HISTORICAL, "HISTORICAL")
        self.assertEqual(EvidenceStatus.INFERRED, "INFERRED")
        self.assertEqual(EvidenceStatus.ANALYST, "ANALYST")
        self.assertEqual(EvidenceStatus.UNKNOWN, "UNKNOWN")
    
    def test_evidence_confidence_choices(self):
        """Test evidence confidence choices."""
        self.assertEqual(Confidence.HIGH, "HIGH")
        self.assertEqual(Confidence.MEDIUM, "MEDIUM")
        self.assertEqual(Confidence.LOW, "LOW")
    
    def test_evidence_metadata(self):
        """Test storing metadata."""
        metadata = {"record_type": "A", "values": ["192.168.1.1"]}
        evidence = Evidence.objects.create(
            domain=self.domain,
            owner=self.user,
            evidence_type=EvidenceType.DNS_OBSERVATION,
            status=EvidenceStatus.OBSERVED,
            confidence=Confidence.HIGH,
            source="DNS Query",
            collection_method="Passive",
            observation="A record found",
            entity_name="example.com",
            entity_type="Domain",
            metadata=metadata,
        )
        self.assertEqual(evidence.metadata, metadata)


class EvidenceRelationshipModelTests(TestCase):
    """Tests for EvidenceRelationship model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.domain = Domain.objects.create(
            name="example.com",
            owner=self.user
        )
        
        self.evidence1 = Evidence.objects.create(
            domain=self.domain,
            owner=self.user,
            evidence_type=EvidenceType.DNS_OBSERVATION,
            status=EvidenceStatus.OBSERVED,
            confidence=Confidence.HIGH,
            source="DNS Query",
            collection_method="Passive",
            observation="A record found",
            entity_name="example.com",
            entity_type="Domain",
        )
        
        self.evidence2 = Evidence.objects.create(
            domain=self.domain,
            owner=self.user,
            evidence_type=EvidenceType.IP_ADDRESS,
            status=EvidenceStatus.OBSERVED,
            confidence=Confidence.HIGH,
            source="RDAP",
            collection_method="Passive",
            observation="IP address found",
            entity_name="192.168.1.1",
            entity_type="IPAddress",
        )
    
    def test_create_evidence_relationship(self):
        """Test creating an evidence relationship."""
        relationship = EvidenceRelationship.objects.create(
            from_evidence=self.evidence1,
            to_evidence=self.evidence2,
            relationship_type="RESOLVES_TO",
            confidence=Confidence.HIGH,
        )
        self.assertEqual(relationship.from_evidence, self.evidence1)
        self.assertEqual(relationship.to_evidence, self.evidence2)
        self.assertEqual(relationship.relationship_type, "RESOLVES_TO")
        self.assertEqual(relationship.confidence, Confidence.HIGH)
    
    def test_evidence_relationship_observed_at(self):
        """Test that observed_at is auto-set."""
        relationship = EvidenceRelationship.objects.create(
            from_evidence=self.evidence1,
            to_evidence=self.evidence2,
            relationship_type="RESOLVES_TO",
            confidence=Confidence.HIGH,
        )
        self.assertIsNotNone(relationship.observed_at)


class LifecycleAssessmentModelTests(TestCase):
    """Tests for LifecycleAssessment model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.domain = Domain.objects.create(
            name="example.com",
            owner=self.user
        )
    
    def test_create_lifecycle_assessment(self):
        """Test creating a lifecycle assessment."""
        assessment = LifecycleAssessment.objects.create(
            domain=self.domain,
            owner=self.user,
            classification=LifecycleAssessment.LifecycleStatus.ACTIVE,
            confidence=0.85,
            supporting_evidence=["evidence-1", "evidence-2"],
            contradicting_evidence=[],
            model_version="1.0",
            explanation="Domain shows regular DNS updates",
        )
        self.assertEqual(assessment.classification, LifecycleAssessment.LifecycleStatus.ACTIVE)
        self.assertEqual(assessment.confidence, 0.85)
        self.assertEqual(len(assessment.supporting_evidence), 2)
        self.assertIsNotNone(assessment.generated_at)
    
    def test_lifecycle_status_choices(self):
        """Test lifecycle status choices."""
        self.assertEqual(LifecycleAssessment.LifecycleStatus.ACTIVE, "ACTIVE")
        self.assertEqual(LifecycleAssessment.LifecycleStatus.LEGACY, "LEGACY")
        self.assertEqual(LifecycleAssessment.LifecycleStatus.POTENTIALLY_ABANDONED, "POTENTIALLY_ABANDONED")
        self.assertEqual(LifecycleAssessment.LifecycleStatus.LIKELY_ABANDONED, "LIKELY_ABANDONED")
        self.assertEqual(LifecycleAssessment.LifecycleStatus.UNKNOWN, "UNKNOWN")
    
    def test_lifecycle_assessment_confidence_range(self):
        """Test that confidence is between 0 and 1."""
        assessment = LifecycleAssessment.objects.create(
            domain=self.domain,
            owner=self.user,
            classification=LifecycleAssessment.LifecycleStatus.ACTIVE,
            confidence=0.95,
            supporting_evidence=[],
            contradicting_evidence=[],
            model_version="1.0",
        )
        self.assertGreaterEqual(assessment.confidence, 0.0)
        self.assertLessEqual(assessment.confidence, 1.0)


class EvidenceAPITests(TestCase):
    """Tests for Evidence API endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.domain = Domain.objects.create(
            name="example.com",
            owner=self.user
        )
        self.client.force_authenticate(user=self.user)
        
        self.evidence = Evidence.objects.create(
            domain=self.domain,
            owner=self.user,
            evidence_type=EvidenceType.DNS_OBSERVATION,
            status=EvidenceStatus.OBSERVED,
            confidence=Confidence.HIGH,
            source="DNS Query",
            collection_method="Passive",
            observation="A record found",
            entity_name="example.com",
            entity_type="Domain",
        )
    
    def test_list_evidence(self):
        """Test listing evidence."""
        response = self.client.get("/api/lifecycle/evidence/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
    
    def test_list_evidence_filtered_by_type(self):
        """Test filtering evidence by type."""
        Evidence.objects.create(
            domain=self.domain,
            owner=self.user,
            evidence_type=EvidenceType.IP_ADDRESS,
            status=EvidenceStatus.OBSERVED,
            confidence=Confidence.HIGH,
            source="RDAP",
            collection_method="Passive",
            observation="IP address",
            entity_name="192.168.1.1",
            entity_type="IPAddress",
        )
        
        response = self.client.get("/api/lifecycle/evidence/?evidence_type=DNS_OBSERVATION")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["evidence_type"], "DNS_OBSERVATION")
    
    def test_list_evidence_filtered_by_status(self):
        """Test filtering evidence by status."""
        Evidence.objects.create(
            domain=self.domain,
            owner=self.user,
            evidence_type=EvidenceType.DNS_OBSERVATION,
            status=EvidenceStatus.HISTORICAL,
            confidence=Confidence.HIGH,
            source="DNS Query",
            collection_method="Passive",
            observation="Old A record",
            entity_name="example.com",
            entity_type="Domain",
        )
        
        response = self.client.get("/api/lifecycle/evidence/?status=OBSERVED")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
    
    def test_list_evidence_filtered_by_confidence(self):
        """Test filtering evidence by confidence."""
        Evidence.objects.create(
            domain=self.domain,
            owner=self.user,
            evidence_type=EvidenceType.IP_ADDRESS,
            status=EvidenceStatus.OBSERVED,
            confidence=Confidence.LOW,
            source="RDAP",
            collection_method="Passive",
            observation="IP address",
            entity_name="192.168.1.1",
            entity_type="IPAddress",
        )
        
        response = self.client.get("/api/lifecycle/evidence/?confidence=HIGH")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
    
    def test_get_evidence(self):
        """Test getting specific evidence."""
        response = self.client.get(f"/api/lifecycle/evidence/{self.evidence.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(self.evidence.id))
    
    def test_get_evidence_for_asset(self):
        """Test getting evidence for a specific asset."""
        response = self.client.get(f"/api/lifecycle/evidence/for_asset/?domain_id={self.domain.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data["results"]), 1)


class EvidenceRelationshipAPITests(TestCase):
    """Tests for EvidenceRelationship API endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.domain = Domain.objects.create(
            name="example.com",
            owner=self.user
        )
        self.client.force_authenticate(user=self.user)
        
        self.evidence1 = Evidence.objects.create(
            domain=self.domain,
            owner=self.user,
            evidence_type=EvidenceType.DNS_OBSERVATION,
            status=EvidenceStatus.OBSERVED,
            confidence=Confidence.HIGH,
            source="DNS Query",
            collection_method="Passive",
            observation="A record found",
            entity_name="example.com",
            entity_type="Domain",
        )
        
        self.evidence2 = Evidence.objects.create(
            domain=self.domain,
            owner=self.user,
            evidence_type=EvidenceType.IP_ADDRESS,
            status=EvidenceStatus.OBSERVED,
            confidence=Confidence.HIGH,
            source="RDAP",
            collection_method="Passive",
            observation="IP address found",
            entity_name="192.168.1.1",
            entity_type="IPAddress",
        )
        
        self.relationship = EvidenceRelationship.objects.create(
            from_evidence=self.evidence1,
            to_evidence=self.evidence2,
            relationship_type="RESOLVES_TO",
            confidence=Confidence.HIGH,
        )
    
    def test_list_evidence_relationships(self):
        """Test listing evidence relationships."""
        response = self.client.get("/api/lifecycle/evidence-relationships/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
    
    def test_create_evidence_relationship(self):
        """Test creating an evidence relationship."""
        evidence3 = Evidence.objects.create(
            domain=self.domain,
            owner=self.user,
            evidence_type=EvidenceType.CERTIFICATE,
            status=EvidenceStatus.OBSERVED,
            confidence=Confidence.HIGH,
            source="CT Log",
            collection_method="Passive",
            observation="Certificate found",
            entity_name="example.com",
            entity_type="Certificate",
        )
        
        response = self.client.post(
            "/api/lifecycle/evidence-relationships/",
            {
                "from_evidence": str(self.evidence1.id),
                "to_evidence": str(evidence3.id),
                "relationship_type": "SECURED_BY",
                "confidence": "HIGH",
            },
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["relationship_type"], "SECURED_BY")
    
    def test_get_evidence_relationship(self):
        """Test getting a specific evidence relationship."""
        response = self.client.get(f"/api/lifecycle/evidence-relationships/{self.relationship.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(self.relationship.id))


class LifecycleAssessmentAPITests(TestCase):
    """Tests for LifecycleAssessment API endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.domain = Domain.objects.create(
            name="example.com",
            owner=self.user
        )
        self.client.force_authenticate(user=self.user)
        
        self.assessment = LifecycleAssessment.objects.create(
            domain=self.domain,
            owner=self.user,
            classification=LifecycleAssessment.LifecycleStatus.ACTIVE,
            confidence=0.85,
            supporting_evidence=["evidence-1"],
            contradicting_evidence=[],
            model_version="1.0",
            explanation="Domain shows regular DNS updates",
        )
    
    def test_list_lifecycle_assessments(self):
        """Test listing lifecycle assessments."""
        response = self.client.get("/api/lifecycle/lifecycle-assessments/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
    
    def test_list_lifecycle_assessments_filtered_by_classification(self):
        """Test filtering assessments by classification."""
        LifecycleAssessment.objects.create(
            domain=self.domain,
            owner=self.user,
            classification=LifecycleAssessment.LifecycleStatus.LEGACY,
            confidence=0.75,
            supporting_evidence=[],
            contradicting_evidence=["evidence-1"],
            model_version="1.0",
            explanation="Domain shows no recent updates",
        )
        
        response = self.client.get("/api/lifecycle/lifecycle-assessments/?classification=ACTIVE")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
    
    def test_get_lifecycle_assessment(self):
        """Test getting a specific lifecycle assessment."""
        response = self.client.get(f"/api/lifecycle/lifecycle-assessments/{self.assessment.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(self.assessment.id))
    
    def test_get_latest_lifecycle_assessment(self):
        """Test getting the latest lifecycle assessment for a domain."""
        response = self.client.get(f"/api/lifecycle/lifecycle-assessments/latest/?domain_id={self.domain.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(self.assessment.id))
    
    def test_classify_domain(self):
        """Test triggering lifecycle classification for a domain."""
        response = self.client.post(
            "/api/lifecycle/lifecycle-assessments/classify/",
            {"domain_id": str(self.domain.id)},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("classification", response.data)
        self.assertIn("confidence", response.data)


class LifecycleClassificationEngineTests(TestCase):
    """Tests for LifecycleClassificationEngine."""
    
    def setUp(self):
        """Set up test data."""
        from apps.dns_intelligence.models import Domain
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.domain = Domain.objects.create(
            name="example.com",
            owner=self.user
        )
    
    def test_classify_domain_no_evidence(self):
        """Test classification with no evidence."""
        result = LifecycleClassificationEngine.classify_domain(self.domain)
        self.assertEqual(result["classification"], "UNKNOWN")
        self.assertLess(result["confidence"], 0.5)
    
    def test_classify_domain_with_dns_evidence(self):
        """Test classification with DNS evidence."""
        from apps.dns_intelligence.models import DNSObservation
        DNSObservation.objects.create(
            domain=self.domain,
            hostname="example.com",
            record_type="A",
            values=["1.2.3.4"],
            response_code="NOERROR",
            source="DNS Resolver",
            confidence="HIGH",
            observed_at=timezone.now() - timedelta(days=10),
        )
        
        result = LifecycleClassificationEngine.classify_domain(self.domain)
        self.assertIn("classification", result)
        self.assertIn("confidence", result)
        self.assertIn("explanation", result)
    
    def test_classify_domain_with_certificate_evidence(self):
        """Test classification with certificate evidence."""
        from apps.certificates.models import CertificateObservation
        Evidence.objects.create(
            domain=self.domain,
            owner=self.user,
            evidence_type=EvidenceType.CERTIFICATE,
            status=EvidenceStatus.OBSERVED,
            confidence=Confidence.HIGH,
            source="TLS Handshake",
            collection_method="Passive",
            observation="Certificate from Let's Encrypt",
            entity_name="example.com",
            entity_type="certificate",
            metadata={
                "issuer": "Let's Encrypt",
                "valid_until": (timezone.now() + timedelta(days=365)).isoformat(),
                "is_expired": False,
            },
            observed_at=timezone.now() - timedelta(days=10),
        )
        
        result = LifecycleClassificationEngine.classify_domain(self.domain)
        self.assertIn("classification", result)
        self.assertIn("supporting_evidence", result)
    
    def test_save_lifecycle_assessment(self):
        """Test saving a lifecycle assessment."""
        classification_result = {
            "classification": "ACTIVE",
            "confidence": 0.85,
            "supporting_evidence": ["evidence-1"],
            "contradicting_evidence": [],
            "limitations": "No significant limitations",
            "explanation": "Domain shows recent activity",
            "model_version": "1.0",
        }
        
        assessment = LifecycleClassificationEngine.save_lifecycle_assessment(
            self.domain,
            classification_result
        )
        
        self.assertEqual(assessment.domain, self.domain)
        self.assertEqual(assessment.classification, "ACTIVE")
        self.assertEqual(assessment.confidence, 0.85)
        self.assertEqual(assessment.model_version, "1.0")
    
    def test_classification_deterministic(self):
        """Test that classification is deterministic."""
        from apps.dns_intelligence.models import DNSObservation
        DNSObservation.objects.create(
            domain=self.domain,
            hostname="example.com",
            record_type="A",
            values=["1.2.3.4"],
            response_code="NOERROR",
            source="DNS Resolver",
            confidence="HIGH",
            observed_at=timezone.now() - timedelta(days=10),
        )
        
        result1 = LifecycleClassificationEngine.classify_domain(self.domain)
        result2 = LifecycleClassificationEngine.classify_domain(self.domain)
        
        self.assertEqual(result1["classification"], result2["classification"])
        self.assertEqual(result1["confidence"], result2["confidence"])
