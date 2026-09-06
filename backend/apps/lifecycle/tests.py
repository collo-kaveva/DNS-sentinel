"""
Tests for lifecycle app - Evidence, EvidenceRelationship, and LifecycleAssessment.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from .models import Evidence, EvidenceRelationship, LifecycleAssessment

User = get_user_model()


class EvidenceModelTests(TestCase):
    """Tests for Evidence model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.domain = User.objects.create_user(
            username="domainuser",
            email="domain@example.com",
            password="testpass123"
        )
        self.domain_id = str(self.domain.id)
    
    def test_create_evidence(self):
        """Test creating evidence."""
        evidence = Evidence.objects.create(
            domain_id=self.domain_id,
            evidence_type=Evidence.EvidenceType.DNS_OBSERVATION,
            status=Evidence.EvidenceStatus.OBSERVED,
            confidence=Evidence.EvidenceConfidence.HIGH,
            source="DNS Query",
            collection_method="Passive",
            observation="A record found",
            entity_name="example.com",
            entity_type="Domain",
        )
        self.assertEqual(evidence.evidence_type, Evidence.EvidenceType.DNS_OBSERVATION)
        self.assertEqual(evidence.status, Evidence.EvidenceStatus.OBSERVED)
        self.assertEqual(evidence.confidence, Evidence.EvidenceConfidence.HIGH)
        self.assertIsNotNone(evidence.observed_at)
    
    def test_evidence_status_choices(self):
        """Test evidence status choices."""
        self.assertEqual(Evidence.EvidenceStatus.OBSERVED, "OBSERVED")
        self.assertEqual(Evidence.EvidenceStatus.HISTORICAL, "HISTORICAL")
        self.assertEqual(Evidence.EvidenceStatus.INFERRED, "INFERRED")
        self.assertEqual(Evidence.EvidenceStatus.ANALYST, "ANALYST")
        self.assertEqual(Evidence.EvidenceStatus.UNKNOWN, "UNKNOWN")
    
    def test_evidence_confidence_choices(self):
        """Test evidence confidence choices."""
        self.assertEqual(Evidence.EvidenceConfidence.HIGH, "HIGH")
        self.assertEqual(Evidence.EvidenceConfidence.MEDIUM, "MEDIUM")
        self.assertEqual(Evidence.EvidenceConfidence.LOW, "LOW")
    
    def test_evidence_metadata(self):
        """Test storing metadata."""
        metadata = {"record_type": "A", "values": ["192.168.1.1"]}
        evidence = Evidence.objects.create(
            domain_id=self.domain_id,
            evidence_type=Evidence.EvidenceType.DNS_OBSERVATION,
            status=Evidence.EvidenceStatus.OBSERVED,
            confidence=Evidence.EvidenceConfidence.HIGH,
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
        self.domain = User.objects.create_user(
            username="domainuser",
            email="domain@example.com",
            password="testpass123"
        )
        self.domain_id = str(self.domain.id)
        
        self.evidence1 = Evidence.objects.create(
            domain_id=self.domain_id,
            evidence_type=Evidence.EvidenceType.DNS_OBSERVATION,
            status=Evidence.EvidenceStatus.OBSERVED,
            confidence=Evidence.EvidenceConfidence.HIGH,
            source="DNS Query",
            collection_method="Passive",
            observation="A record found",
            entity_name="example.com",
            entity_type="Domain",
        )
        
        self.evidence2 = Evidence.objects.create(
            domain_id=self.domain_id,
            evidence_type=Evidence.EvidenceType.IP_ADDRESS,
            status=Evidence.EvidenceStatus.OBSERVED,
            confidence=Evidence.EvidenceConfidence.HIGH,
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
            confidence=Evidence.EvidenceConfidence.HIGH,
        )
        self.assertEqual(relationship.from_evidence, self.evidence1)
        self.assertEqual(relationship.to_evidence, self.evidence2)
        self.assertEqual(relationship.relationship_type, "RESOLVES_TO")
        self.assertEqual(relationship.confidence, Evidence.EvidenceConfidence.HIGH)
    
    def test_evidence_relationship_observed_at(self):
        """Test that observed_at is auto-set."""
        relationship = EvidenceRelationship.objects.create(
            from_evidence=self.evidence1,
            to_evidence=self.evidence2,
            relationship_type="RESOLVES_TO",
            confidence=Evidence.EvidenceConfidence.HIGH,
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
        self.domain = User.objects.create_user(
            username="domainuser",
            email="domain@example.com",
            password="testpass123"
        )
        self.domain_id = str(self.domain.id)
    
    def test_create_lifecycle_assessment(self):
        """Test creating a lifecycle assessment."""
        assessment = LifecycleAssessment.objects.create(
            domain_id=self.domain_id,
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
            domain_id=self.domain_id,
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
        self.domain = User.objects.create_user(
            username="domainuser",
            email="domain@example.com",
            password="testpass123"
        )
        self.domain_id = str(self.domain.id)
        self.client.force_authenticate(user=self.user)
        
        self.evidence = Evidence.objects.create(
            domain_id=self.domain_id,
            evidence_type=Evidence.EvidenceType.DNS_OBSERVATION,
            status=Evidence.EvidenceStatus.OBSERVED,
            confidence=Evidence.EvidenceConfidence.HIGH,
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
            domain_id=self.domain_id,
            evidence_type=Evidence.EvidenceType.IP_ADDRESS,
            status=Evidence.EvidenceStatus.OBSERVED,
            confidence=Evidence.EvidenceConfidence.HIGH,
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
            domain_id=self.domain_id,
            evidence_type=Evidence.EvidenceType.DNS_OBSERVATION,
            status=Evidence.EvidenceStatus.HISTORICAL,
            confidence=Evidence.EvidenceConfidence.HIGH,
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
            domain_id=self.domain_id,
            evidence_type=Evidence.EvidenceType.IP_ADDRESS,
            status=Evidence.EvidenceStatus.OBSERVED,
            confidence=Evidence.EvidenceConfidence.LOW,
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
        response = self.client.get(f"/api/lifecycle/evidence/for_asset/?domain_id={self.domain_id}")
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
        self.domain = User.objects.create_user(
            username="domainuser",
            email="domain@example.com",
            password="testpass123"
        )
        self.domain_id = str(self.domain.id)
        self.client.force_authenticate(user=self.user)
        
        self.evidence1 = Evidence.objects.create(
            domain_id=self.domain_id,
            evidence_type=Evidence.EvidenceType.DNS_OBSERVATION,
            status=Evidence.EvidenceStatus.OBSERVED,
            confidence=Evidence.EvidenceConfidence.HIGH,
            source="DNS Query",
            collection_method="Passive",
            observation="A record found",
            entity_name="example.com",
            entity_type="Domain",
        )
        
        self.evidence2 = Evidence.objects.create(
            domain_id=self.domain_id,
            evidence_type=Evidence.EvidenceType.IP_ADDRESS,
            status=Evidence.EvidenceStatus.OBSERVED,
            confidence=Evidence.EvidenceConfidence.HIGH,
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
            confidence=Evidence.EvidenceConfidence.HIGH,
        )
    
    def test_list_evidence_relationships(self):
        """Test listing evidence relationships."""
        response = self.client.get("/api/lifecycle/evidence-relationships/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
    
    def test_create_evidence_relationship(self):
        """Test creating an evidence relationship."""
        evidence3 = Evidence.objects.create(
            domain_id=self.domain_id,
            evidence_type=Evidence.EvidenceType.CERTIFICATE,
            status=Evidence.EvidenceStatus.OBSERVED,
            confidence=Evidence.EvidenceConfidence.HIGH,
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
        self.domain = User.objects.create_user(
            username="domainuser",
            email="domain@example.com",
            password="testpass123"
        )
        self.domain_id = str(self.domain.id)
        self.client.force_authenticate(user=self.user)
        
        self.assessment = LifecycleAssessment.objects.create(
            domain_id=self.domain_id,
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
            domain_id=self.domain_id,
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
        response = self.client.get(f"/api/lifecycle/lifecycle-assessments/latest/?domain_id={self.domain_id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(self.assessment.id))
