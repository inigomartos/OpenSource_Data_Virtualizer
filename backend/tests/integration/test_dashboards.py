"""Integration tests for Dashboard CRUD endpoints."""

import uuid
import pytest
from httpx import AsyncClient
from app.models.user import User
from app.models.dashboard import Dashboard


@pytest.mark.asyncio
class TestDashboardsCRUD:
    async def test_create_dashboard(self, client: AsyncClient, user_auth_headers: dict):
        response = await client.post(
            "/api/v1/dashboards/",
            json={"title": "Sales Overview", "description": "Monthly sales metrics"},
            headers=user_auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Sales Overview"
        assert data["description"] == "Monthly sales metrics"
        assert data["is_shared"] is False

    async def test_list_dashboards(
        self,
        client: AsyncClient,
        user_auth_headers: dict,
        db_session,
        test_user: User,
    ):
        dashboard = Dashboard(
            id=uuid.uuid4(),
            org_id=test_user.org_id,
            created_by_id=test_user.id,
            title="Test Dashboard",
            is_shared=False,
            layout_config=[],
        )
        db_session.add(dashboard)
        await db_session.flush()

        response = await client.get("/api/v1/dashboards/", headers=user_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1
        titles = [d["title"] for d in data["data"]]
        assert "Test Dashboard" in titles

    async def test_get_dashboard(
        self,
        client: AsyncClient,
        user_auth_headers: dict,
        db_session,
        test_user: User,
    ):
        dashboard = Dashboard(
            id=uuid.uuid4(),
            org_id=test_user.org_id,
            created_by_id=test_user.id,
            title="Detail Dashboard",
            is_shared=False,
            layout_config=[],
        )
        db_session.add(dashboard)
        await db_session.flush()

        response = await client.get(
            f"/api/v1/dashboards/{dashboard.id}",
            headers=user_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Detail Dashboard"
        assert "widgets" in data

    async def test_update_dashboard(
        self,
        client: AsyncClient,
        user_auth_headers: dict,
        db_session,
        test_user: User,
    ):
        dashboard = Dashboard(
            id=uuid.uuid4(),
            org_id=test_user.org_id,
            created_by_id=test_user.id,
            title="Old Title",
            is_shared=False,
            layout_config=[],
        )
        db_session.add(dashboard)
        await db_session.flush()

        response = await client.put(
            f"/api/v1/dashboards/{dashboard.id}",
            json={"title": "New Title", "is_shared": True},
            headers=user_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "New Title"
        assert data["is_shared"] is True

    async def test_delete_dashboard(
        self,
        client: AsyncClient,
        user_auth_headers: dict,
        db_session,
        test_user: User,
    ):
        dashboard = Dashboard(
            id=uuid.uuid4(),
            org_id=test_user.org_id,
            created_by_id=test_user.id,
            title="Delete Me",
            is_shared=False,
            layout_config=[],
        )
        db_session.add(dashboard)
        await db_session.flush()

        response = await client.delete(
            f"/api/v1/dashboards/{dashboard.id}",
            headers=user_auth_headers,
        )
        assert response.status_code == 204

        # Verify it's gone
        response = await client.get(
            f"/api/v1/dashboards/{dashboard.id}",
            headers=user_auth_headers,
        )
        assert response.status_code == 404

    async def test_dashboard_not_found(self, client: AsyncClient, user_auth_headers: dict):
        fake_id = uuid.uuid4()
        response = await client.get(
            f"/api/v1/dashboards/{fake_id}",
            headers=user_auth_headers,
        )
        assert response.status_code == 404
