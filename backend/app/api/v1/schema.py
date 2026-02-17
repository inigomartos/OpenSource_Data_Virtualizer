"""Schema explorer endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.dependencies import get_current_user

router = APIRouter()


@router.get("/{connection_id}")
async def get_schema(connection_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    return {"tables": []}


@router.post("/{connection_id}/refresh")
async def refresh_schema(connection_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    return {"status": "refreshing"}
