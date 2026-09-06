"""
Tests for investigation app - Investigation and AnalystNote.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from .models import Investigation, AnalystNote

User = get_user_model()


class InvestigationModelTests(TestCase):
    """Tests for Investigation model."""
    
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
        # Create a domain-like user (in real app this would be a Domain model)
        # For now, we'll use the user ID as a placeholder for domain_id
        self.domain_id = str(self.domain.id)
    
    def test_create_investigation(self):
        """Test creating an investigation."""
        investigation = Investigation.objects.create(
            owner=self.user,
            domain_id=self.domain_id,
            domain_name="example.com",
            title="Test Investigation",
            description="Test description",
            status=Investigation.Status.OPEN,
            priority=Investigation.Priority.MEDIUM,
        )
        self.assertEqual(investigation.owner, self.user)
        self.assertEqual(investigation.status, Investigation.Status.OPEN)
        self.assertEqual(investigation.priority, Investigation.Priority.MEDIUM)
        self.assertIsNotNone(investigation.created_at)
    
    def test_investigation_status_choices(self):
        """Test investigation status choices."""
        self.assertEqual(Investigation.Status.OPEN, "OPEN")
        self.assertEqual(Investigation.Status.IN_PROGRESS, "IN_PROGRESS")
        self.assertEqual(Investigation.Status.RESOLVED, "RESOLVED")
        self.assertEqual(Investigation.Status.CLOSED, "CLOSED")
        self.assertEqual(Investigation.Status.REOPENED, "REOPENED")
    
    def test_investigation_priority_choices(self):
        """Test investigation priority choices."""
        self.assertEqual(Investigation.Priority.LOW, "LOW")
        self.assertEqual(Investigation.Priority.MEDIUM, "MEDIUM")
        self.assertEqual(Investigation.Priority.HIGH, "HIGH")
        self.assertEqual(Investigation.Priority.CRITICAL, "CRITICAL")
    
    def test_investigation_related_evidence(self):
        """Test storing related evidence IDs."""
        investigation = Investigation.objects.create(
            owner=self.user,
            domain_id=self.domain_id,
            domain_name="example.com",
            title="Test Investigation",
            status=Investigation.Status.OPEN,
            priority=Investigation.Priority.MEDIUM,
            related_evidence=["evidence-1", "evidence-2"],
        )
        self.assertEqual(len(investigation.related_evidence), 2)
        self.assertIn("evidence-1", investigation.related_evidence)
    
    def test_investigation_assigned_analyst(self):
        """Test assigning an analyst."""
        analyst = User.objects.create_user(
            username="analyst",
            email="analyst@example.com",
            password="testpass123"
        )
        investigation = Investigation.objects.create(
            owner=self.user,
            domain_id=self.domain_id,
            domain_name="example.com",
            title="Test Investigation",
            status=Investigation.Status.OPEN,
            priority=Investigation.Priority.MEDIUM,
            assigned_analyst=analyst,
        )
        self.assertEqual(investigation.assigned_analyst, analyst)


class AnalystNoteModelTests(TestCase):
    """Tests for AnalystNote model."""
    
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
        
        self.investigation = Investigation.objects.create(
            owner=self.user,
            domain_id=self.domain_id,
            domain_name="example.com",
            title="Test Investigation",
            status=Investigation.Status.OPEN,
            priority=Investigation.Priority.MEDIUM,
        )
    
    def test_create_analyst_note(self):
        """Test creating an analyst note."""
        note = AnalystNote.objects.create(
            investigation=self.investigation,
            author=self.user,
            content="This is a test note",
        )
        self.assertEqual(note.investigation, self.investigation)
        self.assertEqual(note.author, self.user)
        self.assertEqual(note.content, "This is a test note")
        self.assertIsNotNone(note.created_at)
    
    def test_analyst_note_updated_at(self):
        """Test that updated_at is auto-set."""
        note = AnalystNote.objects.create(
            investigation=self.investigation,
            author=self.user,
            content="Initial note",
        )
        old_updated_at = note.updated_at
        
        note.content = "Updated note"
        note.save()
        
        self.assertGreater(note.updated_at, old_updated_at)
    
    def test_analyst_note_ownership(self):
        """Test that notes are tied to their author."""
        other_user = User.objects.create_user(
            username="otheruser",
            email="other@example.com",
            password="testpass123"
        )
        
        note = AnalystNote.objects.create(
            investigation=self.investigation,
            author=self.user,
            content="My note",
        )
        
        self.assertEqual(note.author, self.user)
        self.assertNotEqual(note.author, other_user)


class InvestigationAPITests(TestCase):
    """Tests for Investigation API endpoints."""
    
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
        
        self.investigation = Investigation.objects.create(
            owner=self.user,
            domain_id=self.domain_id,
            domain_name="example.com",
            title="Test Investigation",
            status=Investigation.Status.OPEN,
            priority=Investigation.Priority.MEDIUM,
        )
    
    def test_list_investigations(self):
        """Test listing investigations."""
        response = self.client.get("/api/investigation/investigations/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
    
    def test_list_investigations_user_isolation(self):
        """Test that users only see their own investigations."""
        other_user = User.objects.create_user(
            username="otheruser",
            email="other@example.com",
            password="testpass123"
        )
        Investigation.objects.create(
            owner=other_user,
            domain_id=self.domain_id,
            domain_name="other.com",
            title="Other Investigation",
            status=Investigation.Status.OPEN,
            priority=Investigation.Priority.MEDIUM,
        )
        
        response = self.client.get("/api/investigation/investigations/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only see the 1 investigation for self.user
        self.assertEqual(len(response.data["results"]), 1)
    
    def test_list_investigations_filtered_by_status(self):
        """Test filtering investigations by status."""
        Investigation.objects.create(
            owner=self.user,
            domain_id=self.domain_id,
            domain_name="example2.com",
            title="Closed Investigation",
            status=Investigation.Status.CLOSED,
            priority=Investigation.Priority.MEDIUM,
        )
        
        response = self.client.get("/api/investigation/investigations/?status=OPEN")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["status"], "OPEN")
    
    def test_get_investigation(self):
        """Test getting a specific investigation."""
        response = self.client.get(f"/api/investigation/investigations/{self.investigation.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(self.investigation.id))
    
    def test_create_investigation(self):
        """Test creating an investigation."""
        response = self.client.post(
            "/api/investigation/investigations/",
            {
                "domain": self.domain_id,
                "title": "New Investigation",
                "description": "New description",
                "priority": "HIGH",
            },
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "New Investigation")
        self.assertEqual(response.data["priority"], "HIGH")
    
    def test_update_investigation(self):
        """Test updating an investigation."""
        response = self.client.patch(
            f"/api/investigation/investigations/{self.investigation.id}/",
            {"title": "Updated Title", "status": "IN_PROGRESS"},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Updated Title")
        self.assertEqual(response.data["status"], "IN_PROGRESS")
    
    def test_change_investigation_status(self):
        """Test changing investigation status via custom action."""
        response = self.client.post(
            f"/api/investigation/investigations/{self.investigation.id}/change_status/",
            {"status": "RESOLVED"},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "RESOLVED")
        
        # Verify in database
        self.investigation.refresh_from_db()
        self.assertEqual(self.investigation.status, Investigation.Status.RESOLVED)
    
    def test_assign_investigation(self):
        """Test assigning an analyst to an investigation."""
        analyst = User.objects.create_user(
            username="analyst",
            email="analyst@example.com",
            password="testpass123"
        )
        
        response = self.client.post(
            f"/api/investigation/investigations/{self.investigation.id}/assign/",
            {"analyst_id": str(analyst.id)},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["assigned_analyst"], analyst.id)
        
        # Verify in database
        self.investigation.refresh_from_db()
        self.assertEqual(self.investigation.assigned_analyst, analyst)
    
    def test_get_investigation_timeline(self):
        """Test getting investigation timeline."""
        response = self.client.get(f"/api/investigation/investigations/{self.investigation.id}/timeline/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("timeline", response.data)
        self.assertIn("investigation_id", response.data)
    
    def test_get_related_evidence(self):
        """Test getting related evidence."""
        self.investigation.related_evidence = ["evidence-1", "evidence-2"]
        self.investigation.save()
        
        response = self.client.get(f"/api/investigation/investigations/{self.investigation.id}/related_evidence/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("related_evidence", response.data)
        self.assertEqual(len(response.data["related_evidence"]), 2)


class AnalystNoteAPITests(TestCase):
    """Tests for AnalystNote API endpoints."""
    
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
        
        self.investigation = Investigation.objects.create(
            owner=self.user,
            domain_id=self.domain_id,
            domain_name="example.com",
            title="Test Investigation",
            status=Investigation.Status.OPEN,
            priority=Investigation.Priority.MEDIUM,
        )
        
        self.note = AnalystNote.objects.create(
            investigation=self.investigation,
            author=self.user,
            content="Test note",
        )
    
    def test_list_analyst_notes(self):
        """Test listing analyst notes."""
        response = self.client.get("/api/investigation/analyst-notes/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
    
    def test_list_analyst_notes_filtered_by_investigation(self):
        """Test filtering notes by investigation."""
        other_investigation = Investigation.objects.create(
            owner=self.user,
            domain_id=self.domain_id,
            domain_name="other.com",
            title="Other Investigation",
            status=Investigation.Status.OPEN,
            priority=Investigation.Priority.MEDIUM,
        )
        AnalystNote.objects.create(
            investigation=other_investigation,
            author=self.user,
            content="Other note",
        )
        
        response = self.client.get(f"/api/investigation/analyst-notes/?investigation={self.investigation.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
    
    def test_get_analyst_note(self):
        """Test getting a specific analyst note."""
        response = self.client.get(f"/api/investigation/analyst-notes/{self.note.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(self.note.id))
    
    def test_create_analyst_note(self):
        """Test creating an analyst note."""
        response = self.client.post(
            "/api/investigation/analyst-notes/",
            {
                "investigation": str(self.investigation.id),
                "content": "New note",
            },
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["content"], "New note")
    
    def test_update_analyst_note(self):
        """Test updating an analyst note."""
        response = self.client.patch(
            f"/api/investigation/analyst-notes/{self.note.id}/",
            {"content": "Updated note"},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["content"], "Updated note")
    
    def test_update_analyst_note_ownership(self):
        """Test that users can only update their own notes."""
        other_user = User.objects.create_user(
            username="otheruser",
            email="other@example.com",
            password="testpass123"
        )
        other_client = APIClient()
        other_client.force_authenticate(user=other_user)
        
        response = other_client.patch(
            f"/api/investigation/analyst-notes/{self.note.id}/",
            {"content": "Hacked note"},
            format="json"
        )
        # Should be forbidden
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_delete_analyst_note(self):
        """Test deleting an analyst note."""
        response = self.client.delete(f"/api/investigation/analyst-notes/{self.note.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify it's deleted
        self.assertFalse(AnalystNote.objects.filter(id=self.note.id).exists())
    
    def test_delete_analyst_note_ownership(self):
        """Test that users can only delete their own notes."""
        other_user = User.objects.create_user(
            username="otheruser",
            email="other@example.com",
            password="testpass123"
        )
        other_client = APIClient()
        other_client.force_authenticate(user=other_user)
        
        response = other_client.delete(f"/api/investigation/analyst-notes/{self.note.id}/")
        # Should be forbidden
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Verify it's not deleted
        self.assertTrue(AnalystNote.objects.filter(id=self.note.id).exists())
