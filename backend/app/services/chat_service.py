"""Chat session and message management."""

import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.chat_session import ChatSession
from app.models.chat_message import ChatMessage


class ChatService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_session(
        self, user_id: str, connection_id: str, session_id: str = None
    ) -> ChatSession:
        """Get existing session or create new one."""
        if session_id:
            result = await self.db.execute(
                select(ChatSession).where(
                    ChatSession.id == session_id,
                    ChatSession.user_id == user_id,
                )
            )
            session = result.scalar_one_or_none()
            if session:
                return session

        session = ChatSession(
            user_id=user_id,
            connection_id=connection_id,
            title="New Chat",
        )
        self.db.add(session)
        await self.db.flush()
        return session

    async def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        **kwargs,
    ) -> ChatMessage:
        """Save a chat message."""
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            generated_sql=kwargs.get("generated_sql"),
            sql_was_executed=kwargs.get("sql_was_executed", False),
            query_result_preview=kwargs.get("query_result_preview"),
            full_result_row_count=kwargs.get("full_result_row_count"),
            chart_config=kwargs.get("chart_config"),
            execution_time_ms=kwargs.get("execution_time_ms"),
            error_message=kwargs.get("error_message"),
            token_usage=kwargs.get("token_usage"),
            context_summary=kwargs.get("context_summary"),
        )
        self.db.add(message)
        await self.db.flush()
        return message

    async def get_session_messages(self, session_id: str, limit: int = 50) -> list[ChatMessage]:
        """Get messages for a session."""
        result = await self.db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_user_sessions(self, user_id: str) -> list[ChatSession]:
        """Get all sessions for a user."""
        result = await self.db.execute(
            select(ChatSession)
            .where(ChatSession.user_id == user_id)
            .order_by(ChatSession.created_at.desc())
        )
        return list(result.scalars().all())

    async def update_session_title(self, session_id: str, title: str) -> None:
        """Update session title (usually auto-generated from first message)."""
        result = await self.db.execute(
            select(ChatSession).where(ChatSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        if session:
            session.title = title
