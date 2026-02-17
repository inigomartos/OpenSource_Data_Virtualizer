"""Auth API integration tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestAuthAPI:
    async def test_register_success(self, client: AsyncClient):
        response = await client.post("/api/v1/auth/register", json={
            "email": "admin@novatech.com",
            "password": "securepassword123",
            "full_name": "Admin User",
            "org_name": "NovaTech Manufacturing",
            "org_slug": "novatech",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "admin@novatech.com"
        assert data["role"] == "admin"

    async def test_login_success(self, client: AsyncClient):
        # First register
        await client.post("/api/v1/auth/register", json={
            "email": "test@test.com",
            "password": "testpassword123",
            "full_name": "Test User",
            "org_name": "Test Org",
            "org_slug": "test-org",
        })

        # Then login
        response = await client.post("/api/v1/auth/login", json={
            "email": "test@test.com",
            "password": "testpassword123",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_login_wrong_password(self, client: AsyncClient):
        await client.post("/api/v1/auth/register", json={
            "email": "wrong@test.com",
            "password": "correctpassword",
            "full_name": "Wrong Pass",
            "org_name": "Test Org 2",
            "org_slug": "test-org-2",
        })

        response = await client.post("/api/v1/auth/login", json={
            "email": "wrong@test.com",
            "password": "wrongpassword",
        })
        assert response.status_code == 401

    async def test_health_check(self, client: AsyncClient):
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
