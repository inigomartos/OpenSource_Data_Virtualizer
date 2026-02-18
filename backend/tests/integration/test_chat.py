"""Integration tests for Chat session and history endpoints."""

import uuid
import pytest
from httpx import AsyncClient
from app.models.user import User
from app.models.connection import Connection
from app.models.chat_session import ChatSession
from app.models.chat_message import ChatMessage


@pytest.mark.asyncio
class TestChatEndpoints:
    async def test_list_sessions_empty(self, client: AsyncClient, user_auth_headers: dict):
        response = await client.get("/api/v1/chat/sessions", headers=user_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["data"] == []

    async def test_list_sessions_with_data(
        self,
        client: AsyncClient,
        user_auth_headers: dict,
        db_session,
        test_user: User,
        test_connection: Connection,
    ):
        session = ChatSession(
            id=uuid.uuid4(),
            user_id=test_user.id,
            connection_id=test_connection.id,
            title="Test chat",
            is_pinned=False,
        )
        db_session.add(session)
        await db_session.flush()

        response = await client.get("/api/v1/chat/sessions", headers=user_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["data"][0]["title"] == "Test chat"

    async def test_get_history(
        self,
        client: AsyncClient,
        user_auth_headers: dict,
        db_session,
        test_user: User,
        test_connection: Connection,
    ):
        session = ChatSession(
            id=uuid.uuid4(),
            user_id=test_user.id,
            connection_id=test_connection.id,
            title="History test",
            is_pinned=False,
        )
        db_session.add(session)
        await db_session.flush()

        msg = ChatMessage(
            id=uuid.uuid4(),
            session_id=session.id,
            role="user",
            content="Hello AI",
        )
        db_session.add(msg)
        await db_session.flush()

        response = await client.get(
            f"/api/v1/chat/history/{session.id}",
            headers=user_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["data"][0]["content"] == "Hello AI"
        assert data["data"][0]["role"] == "user"

    async def test_delete_session(
        self,
        client: AsyncClient,
        user_auth_headers: dict,
        db_session,
        test_user: User,
        test_connection: Connection,
    ):
        session = ChatSession(
            id=uuid.uuid4(),
            user_id=test_user.id,
            connection_id=test_connection.id,
            title="Delete me",
            is_pinned=False,
        )
        db_session.add(session)
        await db_session.flush()

        response = await client.delete(
            f"/api/v1/chat/sessions/{session.id}",
            headers=user_auth_headers,
        )
        assert response.status_code == 204

        # Verify it's gone
        response = await client.get("/api/v1/chat/sessions", headers=user_auth_headers)
        assert response.json()["count"] == 0

    async def test_update_session(
        self,
        client: AsyncClient,
        user_auth_headers: dict,
        db_session,
        test_user: User,
        test_connection: Connection,
    ):
        session = ChatSession(
            id=uuid.uuid4(),
            user_id=test_user.id,
            connection_id=test_connection.id,
            title="Original title",
            is_pinned=False,
        )
        db_session.add(session)
        await db_session.flush()

        response = await client.patch(
            f"/api/v1/chat/sessions/{session.id}",
            json={"title": "Renamed session", "is_pinned": True},
            headers=user_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Renamed session"
        assert data["is_pinned"] is True

    async def test_history_404_for_wrong_user(
        self,
        client: AsyncClient,
        db_session,
        test_user: User,
        test_connection: Connection,
    ):
        """A session belonging to user A should 404 for user B."""
        from app.core.security import create_access_token

        session = ChatSession(
            id=uuid.uuid4(),
            user_id=test_user.id,
            connection_id=test_connection.id,
            title="Private",
            is_pinned=False,
        )
        db_session.add(session)
        await db_session.flush()

        # Create token for a different user
        other_token = create_access_token({
            "sub": str(uuid.uuid4()),
            "org_id": str(test_user.org_id),
            "email": "other@test.com",
            "role": "analyst",
        })
        other_headers = {"Authorization": f"Bearer {other_token}"}

        response = await client.get(
            f"/api/v1/chat/history/{session.id}",
            headers=other_headers,
        )
        assert response.status_code == 404
