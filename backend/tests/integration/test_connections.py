"""Integration tests for Connection CRUD endpoints."""

import uuid
import pytest
from httpx import AsyncClient
from app.models.organization import Organization
from app.models.user import User
from app.models.connection import Connection
from app.core.security import create_access_token


@pytest.mark.asyncio
class TestConnectionsCRUD:
    async def test_create_connection(self, client: AsyncClient, user_auth_headers: dict):
        response = await client.post(
            "/api/v1/connections/",
            json={
                "name": "My PostgreSQL",
                "type": "postgresql",
                "host": "db.example.com",
                "port": 5432,
                "database_name": "mydb",
                "username": "admin",
            },
            headers=user_auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "My PostgreSQL"
        assert data["type"] == "postgresql"
        assert data["is_active"] is True
        # Password should NOT be in response
        assert "password_encrypted" not in data

    async def test_list_connections(
        self, client: AsyncClient, user_auth_headers: dict, test_connection: Connection,
    ):
        response = await client.get("/api/v1/connections/", headers=user_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1
        names = [c["name"] for c in data["data"]]
        assert "Test PostgreSQL" in names

    async def test_get_single_connection(
        self, client: AsyncClient, user_auth_headers: dict, test_connection: Connection,
    ):
        response = await client.get(
            f"/api/v1/connections/{test_connection.id}",
            headers=user_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test PostgreSQL"

    async def test_delete_connection(
        self, client: AsyncClient, user_auth_headers: dict, test_connection: Connection,
    ):
        response = await client.delete(
            f"/api/v1/connections/{test_connection.id}",
            headers=user_auth_headers,
        )
        assert response.status_code == 204

        # Verify it's gone
        response = await client.get(
            f"/api/v1/connections/{test_connection.id}",
            headers=user_auth_headers,
        )
        assert response.status_code == 404

    async def test_org_scoping(
        self, client: AsyncClient, db_session, test_connection: Connection,
    ):
        """Org A's user should not see Org B's connections."""
        # Create a second org + user
        org_b = Organization(id=uuid.uuid4(), name="Org B", slug="org-b")
        db_session.add(org_b)
        await db_session.flush()

        user_b = User(
            id=uuid.uuid4(),
            org_id=org_b.id,
            email="userb@orgb.com",
            password_hash="fakehash",
            full_name="User B",
            role="admin",
        )
        db_session.add(user_b)
        await db_session.flush()

        token_b = create_access_token({
            "sub": str(user_b.id),
            "org_id": str(org_b.id),
            "email": user_b.email,
            "role": user_b.role,
        })
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # User B should NOT see test_connection (belongs to Org A)
        response = await client.get("/api/v1/connections/", headers=headers_b)
        assert response.status_code == 200
        assert response.json()["count"] == 0

    async def test_unauthenticated_request(self, client: AsyncClient):
        response = await client.get("/api/v1/connections/")
        assert response.status_code in (401, 422)
