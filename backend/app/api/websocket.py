"""WebSocket endpoint with JWT auth, AI streaming, and Redis PubSub for multi-replica support."""

import asyncio
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from sqlalchemy import select

from app.core.security import decode_jwt, is_token_blacklisted
from app.core.database import async_session_factory
from app.core.sql_validator import SQLSafetyValidator
from app.models.chat_session import ChatSession
from app.models.chat_message import ChatMessage
from app.models.user import User
from app.schemas.chat import ChatResponse
from app.services.ai_engine import AIEngine
from app.services.cache_service import CacheService
from app.services.connection_manager import ConnectionManager
from app.services.query_executor import QueryExecutor
from app.services.schema_discoverer import SchemaDiscoverer
from app.ai.conversation import ConversationManager
from loguru import logger
import json

websocket_router = APIRouter()

WS_PUBSUB_CHANNEL = "datamind:ws:broadcast"


class ConnectionManagerWS:
    """Manages active WebSocket connections with Redis PubSub for cross-replica delivery."""

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self._redis = None
        self._pubsub = None
        self._listener_task: Optional[asyncio.Task] = None

    async def initialize(self):
        """Connect to Redis PubSub. Call once at app startup."""
        try:
            import redis.asyncio as aioredis
            from app.config import settings
            self._redis = aioredis.from_url(
                settings.REDIS_URL, socket_connect_timeout=2,
            )
            self._pubsub = self._redis.pubsub()
            await self._pubsub.subscribe(WS_PUBSUB_CHANNEL)
            self._listener_task = asyncio.create_task(self._listen())
            logger.info("WebSocket Redis PubSub initialized")
        except Exception as e:
            logger.warning(f"Redis PubSub init failed (local-only mode): {e}")
            self._redis = None
            self._pubsub = None

    async def shutdown(self):
        """Cleanup on app shutdown."""
        if self._listener_task:
            self._listener_task.cancel()
        if self._pubsub:
            await self._pubsub.unsubscribe(WS_PUBSUB_CHANNEL)
            await self._pubsub.aclose()
        if self._redis:
            await self._redis.aclose()

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"WebSocket connected: user {user_id}")

    def disconnect(self, user_id: str):
        self.active_connections.pop(user_id, None)
        logger.info(f"WebSocket disconnected: user {user_id}")

    async def send_to_user(self, user_id: str, data: dict):
        """Send to local connection first; if not found, publish to Redis for other replicas."""
        ws = self.active_connections.get(user_id)
        if ws:
            await ws.send_json(data)
        elif self._redis:
            try:
                payload = json.dumps({"user_id": user_id, "data": data})
                await self._redis.publish(WS_PUBSUB_CHANNEL, payload)
            except Exception as e:
                logger.warning(f"Failed to publish WS message via Redis: {e}")

    async def _listen(self):
        """Background task: listen for messages from other replicas."""
        try:
            async for message in self._pubsub.listen():
                if message["type"] != "message":
                    continue
                try:
                    payload = json.loads(message["data"])
                    target_user = payload.get("user_id")
                    data = payload.get("data")
                    ws = self.active_connections.get(target_user)
                    if ws:
                        await ws.send_json(data)
                except Exception as e:
                    logger.debug(f"PubSub message parse error: {e}")
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"PubSub listener error: {e}")


ws_manager = ConnectionManagerWS()


async def _authenticate_ws(
    websocket: WebSocket, token: Optional[str]
) -> Optional[str]:
    """Authenticate via query-param token or HttpOnly cookie. Returns user_id."""
    ws_token = token
    if not ws_token:
        ws_token = websocket.cookies.get("access_token")
    if not ws_token:
        return None
    try:
        payload = decode_jwt(ws_token)
        if payload.get("type") != "access":
            return None
        jti = payload.get("jti")
        if jti and await is_token_blacklisted(jti):
            return None
        return payload.get("sub")
    except Exception:
        return None


@websocket_router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket, token: Optional[str] = Query(default=None)
):
    """WebSocket endpoint with JWT authentication on handshake."""
    user_id = await _authenticate_ws(websocket, token)
    if not user_id:
        await websocket.close(code=4001, reason="Authentication failed")
        return

    await ws_manager.connect(user_id, websocket)

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            event_type = message.get("type")

            if event_type == "ping":
                await websocket.send_json({"type": "pong"})
            elif event_type == "chat_message":
                await _handle_chat_message(websocket, user_id, message)
            elif event_type == "cancel_query":
                logger.info(f"Query cancel requested by user {user_id}")
            else:
                logger.debug(f"Unknown WS event from {user_id}: {event_type}")

    except WebSocketDisconnect:
        ws_manager.disconnect(user_id)
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        ws_manager.disconnect(user_id)


async def _handle_chat_message(
    websocket: WebSocket, user_id: str, message: dict
):
    """Handle incoming chat message: run AI pipeline with streaming."""
    user_text = message.get("message", "").strip()
    connection_id = message.get("connection_id")
    session_id = message.get("session_id")

    if not user_text or not connection_id:
        await websocket.send_json({
            "type": "error",
            "content": "Missing message or connection_id.",
        })
        return

    async def on_stream(event: dict):
        """Stream callback — sends each text chunk to the client."""
        await websocket.send_json({
            "type": "stream",
            "phase": event.get("phase", ""),
            "chunk": event.get("chunk", ""),
        })

    async with async_session_factory() as db:
        try:
            # Fetch user
            result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            if not user:
                await websocket.send_json({
                    "type": "error", "content": "User not found.",
                })
                return

            # Resolve or create chat session
            if session_id:
                sess_result = await db.execute(
                    select(ChatSession).where(
                        ChatSession.id == session_id,
                        ChatSession.user_id == user.id,
                    )
                )
                session = sess_result.scalar_one_or_none()
                if not session:
                    await websocket.send_json({
                        "type": "error", "content": "Session not found.",
                    })
                    return
            else:
                title = (
                    user_text[:80]
                    if len(user_text) <= 80
                    else user_text[:77] + "..."
                )
                session = ChatSession(
                    user_id=user.id,
                    connection_id=connection_id,
                    title=title,
                    is_pinned=False,
                )
                db.add(session)
                await db.flush()
                await db.refresh(session)

            # Persist user message
            user_msg = ChatMessage(
                session_id=session.id,
                role="user",
                content=user_text,
            )
            db.add(user_msg)
            await db.flush()
            await db.refresh(user_msg)

            # Notify client that streaming has started
            await websocket.send_json({
                "type": "stream_start",
                "session_id": str(session.id),
                "message_id": str(user_msg.id),
            })

            # Build AIEngine (same dependencies as REST endpoint)
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

            ai_response = await ai_engine.process_message(
                user_message=user_text,
                connection_id=str(connection_id),
                session_id=str(session.id),
                db=db,
                on_stream=on_stream,
                org_id=str(user.org_id),
            )

            # Persist assistant response
            assistant_msg = ChatMessage(
                session_id=session.id,
                role="assistant",
                content=ai_response.content,
                generated_sql=ai_response.generated_sql,
                sql_was_executed=(
                    ai_response.generated_sql is not None
                    and ai_response.error_message is None
                ),
                query_result_preview=ai_response.query_result_preview,
                full_result_row_count=ai_response.full_result_row_count,
                chart_config=ai_response.chart_config,
                execution_time_ms=ai_response.execution_time_ms,
                error_message=ai_response.error_message,
                token_usage=ai_response.token_usage,
                context_summary=ai_response.context_summary,
            )
            db.add(assistant_msg)
            await db.flush()
            await db.refresh(assistant_msg)
            await db.commit()

            # Send final complete response
            await websocket.send_json({
                "type": "chat_response",
                "session_id": str(session.id),
                "message_id": str(assistant_msg.id),
                "content": ai_response.content,
                "context_summary": ai_response.context_summary,
                "generated_sql": ai_response.generated_sql,
                "query_result_preview": ai_response.query_result_preview,
                "full_result_row_count": ai_response.full_result_row_count,
                "chart_config": ai_response.chart_config,
                "execution_time_ms": ai_response.execution_time_ms,
                "token_usage": ai_response.token_usage,
                "error_message": ai_response.error_message,
            })

        except Exception as e:
            logger.error(f"Chat pipeline error for user {user_id}: {e}")
            await db.rollback()
            await websocket.send_json({
                "type": "chat_response",
                "content": f"I encountered an error: {str(e)}",
                "error_message": str(e),
            })
