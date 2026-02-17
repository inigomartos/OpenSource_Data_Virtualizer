"""WebSocket endpoint with JWT-authenticated handshake."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.core.security import decode_jwt
from loguru import logger
import json

websocket_router = APIRouter()


class ConnectionManagerWS:
    """Manages active WebSocket connections."""

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"WebSocket connected: user {user_id}")

    def disconnect(self, user_id: str):
        self.active_connections.pop(user_id, None)
        logger.info(f"WebSocket disconnected: user {user_id}")

    async def send_to_user(self, user_id: str, data: dict):
        ws = self.active_connections.get(user_id)
        if ws:
            await ws.send_json(data)


ws_manager = ConnectionManagerWS()


@websocket_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    """WebSocket endpoint with JWT authentication on handshake."""
    try:
        payload = decode_jwt(token)
        if payload.get("type") != "access":
            await websocket.close(code=4001, reason="Invalid token type")
            return
        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=4001, reason="Invalid token")
            return
    except Exception:
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
            elif event_type == "cancel_query":
                logger.info(f"Query cancel requested by user {user_id}")
            else:
                logger.debug(f"Unknown WS event from {user_id}: {event_type}")

    except WebSocketDisconnect:
        ws_manager.disconnect(user_id)
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        ws_manager.disconnect(user_id)
