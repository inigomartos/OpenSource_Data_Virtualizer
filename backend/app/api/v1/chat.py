"""Chat endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.dependencies import get_current_user

router = APIRouter()


@router.post("/message")
async def send_message(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    return {"message": "Response placeholder"}


@router.get("/history/{session_id}")
async def get_history(session_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    return {"messages": []}


@router.get("/sessions")
async def list_sessions(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    return {"sessions": []}
