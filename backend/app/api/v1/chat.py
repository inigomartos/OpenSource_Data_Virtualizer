"""Chat REST endpoints.

Provides CRUD operations for chat sessions and messages, including
AI-powered responses via the AIEngine pipeline.

All queries are scoped to the current user (``user.id``) for security.
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.exceptions import raise_not_found, raise_forbidden
from app.core.sql_validator import SQLSafetyValidator
from app.dependencies import get_current_user
from app.models.chat_session import ChatSession
from app.models.chat_message import ChatMessage
from app.models.user import User
from app.schemas.chat import (
    ChatMessageRequest,
    ChatMessageResponse,
    ChatResponse,
    ChatSessionResponse,
    ChatSessionUpdate,
)
from app.schemas.common import ListResponse
from app.services.ai_engine import AIEngine
from app.services.cache_service import CacheService
from app.services.connection_manager import ConnectionManager
from app.services.query_executor import QueryExecutor
from app.services.schema_discoverer import SchemaDiscoverer
from app.ai.conversation import ConversationManager
from loguru import logger

router = APIRouter()


# ── Helpers ──────────────────────────────────────────────────────────────────

async def _get_session_or_404(
    session_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> ChatSession:
    """Fetch a chat session owned by the user, or raise 404."""
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise_not_found("ChatSession")
    return session


# ── Message Endpoints ────────────────────────────────────────────────────────

@router.post("/message", response_model=ChatResponse)
async def send_message(
    payload: ChatMessageRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Accept a user message, persist it, and return an AI-generated response.

    If ``session_id`` is omitted a new session is created automatically.
    The AIEngine pipeline: schema context -> NL-to-SQL -> execute -> analyze.
    """
    # Resolve or create chat session
    if payload.session_id:
        session = await _get_session_or_404(payload.session_id, user.id, db)
    else:
        # Auto-generate a title from the first message
        title = payload.message[:80] if len(payload.message) <= 80 else payload.message[:77] + "..."
        session = ChatSession(
            user_id=user.id,
            connection_id=payload.connection_id,
            title=title,
            is_pinned=False,
        )
        db.add(session)
        await db.flush()
        await db.refresh(session)

    # Persist the user's message
    user_message = ChatMessage(
        session_id=session.id,
        role="user",
        content=payload.message,
    )
    db.add(user_message)
    await db.flush()
    await db.refresh(user_message)

    # Run the AI pipeline
    connection_manager = ConnectionManager()
    schema_discoverer = SchemaDiscoverer()
    query_executor = QueryExecutor(connection_manager)
    cache_service = CacheService()
    conversation_manager = ConversationManager()
    sql_validator = SQLSafetyValidator()

    ai_engine = AIEngine(
        schema_provider=schema_discoverer,
        query_runner=query_executor,
        sql_validator=sql_validator,
        cache_provider=cache_service,
        conversation_provider=conversation_manager,
    )

    try:
        ai_response = await ai_engine.process_message(
            user_message=payload.message,
            connection_id=str(payload.connection_id),
            session_id=str(session.id),
            db=db,
        )
    except Exception as e:
        logger.error(f"AIEngine error for session {session.id}: {e}")
        ai_response = ChatResponse(
            content=f"I encountered an error processing your request: {str(e)}",
            error_message=str(e),
        )

    # Persist the assistant response with all AI metadata
    assistant_message = ChatMessage(
        session_id=session.id,
        role="assistant",
        content=ai_response.content,
        generated_sql=ai_response.generated_sql,
        sql_was_executed=ai_response.generated_sql is not None and ai_response.error_message is None,
        query_result_preview=ai_response.query_result_preview,
        full_result_row_count=ai_response.full_result_row_count,
        chart_config=ai_response.chart_config,
        execution_time_ms=ai_response.execution_time_ms,
        error_message=ai_response.error_message,
        token_usage=ai_response.token_usage,
        context_summary=ai_response.context_summary,
    )
    db.add(assistant_message)
    await db.flush()
    await db.refresh(assistant_message)

    return ChatResponse(
        content=ai_response.content,
        context_summary=ai_response.context_summary,
        generated_sql=ai_response.generated_sql,
        query_result_preview=ai_response.query_result_preview,
        full_result_row_count=ai_response.full_result_row_count,
        chart_config=ai_response.chart_config,
        execution_time_ms=ai_response.execution_time_ms,
        token_usage=ai_response.token_usage,
        error_message=ai_response.error_message,
        session_id=session.id,
        message_id=assistant_message.id,
    )


@router.get(
    "/history/{session_id}",
    response_model=ListResponse[ChatMessageResponse],
)
async def get_history(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Return all messages for a chat session, ordered chronologically."""
    # Verify session belongs to caller
    await _get_session_or_404(session_id, user.id, db)

    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
    )
    messages = result.scalars().all()
    return {"data": messages, "count": len(messages)}


# ── Session Endpoints ────────────────────────────────────────────────────────

@router.get("/sessions", response_model=ListResponse[ChatSessionResponse])
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List all chat sessions owned by the current user."""
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == user.id)
        .order_by(ChatSession.updated_at.desc())
    )
    sessions = result.scalars().all()
    return {"data": sessions, "count": len(sessions)}


@router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Delete a chat session and all its messages (cascade)."""
    session = await _get_session_or_404(session_id, user.id, db)
    await db.delete(session)
    await db.flush()
    return None


@router.patch("/sessions/{session_id}", response_model=ChatSessionResponse)
async def update_session(
    session_id: uuid.UUID,
    payload: ChatSessionUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update a chat session (rename, pin/unpin)."""
    session = await _get_session_or_404(session_id, user.id, db)

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(session, field, value)

    await db.flush()
    await db.refresh(session)
    return session
