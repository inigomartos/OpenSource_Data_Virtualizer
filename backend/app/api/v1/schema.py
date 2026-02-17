"""Schema explorer endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.exceptions import raise_not_found
from app.dependencies import get_current_user
from app.models.connection import Connection
from app.models.user import User

router = APIRouter()


@router.get("/{connection_id}")
async def get_schema(connection_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    conn_result = await db.execute(
        select(Connection).where(Connection.id == connection_id, Connection.org_id == user.org_id)
    )
    if not conn_result.scalar_one_or_none():
        raise_not_found("Connection")
    return {"tables": []}


@router.post("/{connection_id}/refresh")
async def refresh_schema(connection_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    conn_result = await db.execute(
        select(Connection).where(Connection.id == connection_id, Connection.org_id == user.org_id)
    )
    if not conn_result.scalar_one_or_none():
        raise_not_found("Connection")
    return {"status": "refreshing"}
