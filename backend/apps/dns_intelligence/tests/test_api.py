import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="tester", password="Str0ngPassw0rd!")


@pytest.fixture
def auth_client(api_client, user):
    from rest_framework.authtoken.models import Token
    token, _ = Token.objects.get_or_create(user=user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return api_client


@pytest.mark.django_db
class TestAuth:
    def test_register_creates_user_and_token(self, api_client):
        resp = api_client.post("/api/auth/register/", {
            "username": "newanalyst", "email": "n@example.com", "password": "Str0ngPassw0rd!",
        })
        assert resp.status_code == 201
        assert "token" in resp.data

    def test_register_rejects_weak_password(self, api_client):
        resp = api_client.post("/api/auth/register/", {
            "username": "weakuser", "password": "12345",
        })
        assert resp.status_code == 400

    def test_login_returns_token(self, api_client, user):
        resp = api_client.post("/api/auth/login/", {
            "username": "tester", "password": "Str0ngPassw0rd!",
        })
        assert resp.status_code == 200
        assert "token" in resp.data


@pytest.mark.django_db
class TestDomains:
    def test_unauthenticated_cannot_list_domains(self, api_client):
        resp = api_client.get("/api/domains/")
        assert resp.status_code == 401

    def test_create_domain_requires_authorization_flag(self, auth_client):
        resp = auth_client.post("/api/domains/", {"name": "example.com", "authorized": False})
        assert resp.status_code == 400

    def test_create_and_list_domain(self, auth_client):
        resp = auth_client.post("/api/domains/", {"name": "example.com", "authorized": True})
        assert resp.status_code == 201
        resp2 = auth_client.get("/api/domains/")
        assert resp2.status_code == 200
        assert resp2.data["count"] == 1

    def test_domain_scoped_to_owner(self, api_client, user, db):
        other = User.objects.create_user(username="other", password="Str0ngPassw0rd!")
        from apps.dns_intelligence.models import Domain
        Domain.objects.create(owner=other, name="private.com", authorized=True)

        from rest_framework.authtoken.models import Token
        token, _ = Token.objects.get_or_create(user=user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        resp = api_client.get("/api/domains/")
        assert resp.data["count"] == 0

    def test_investigate_unauthorized_domain_forbidden(self, auth_client, db, user):
        from apps.dns_intelligence.models import Domain
        d = Domain.objects.create(owner=user, name="unauth.com", authorized=False)
        resp = auth_client.post(f"/api/domains/{d.id}/investigate/")
        assert resp.status_code == 403
