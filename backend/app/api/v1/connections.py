"""Connection CRUD endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.dependencies import get_current_user

router = APIRouter()


@router.get("/")
async def list_connections(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    return {"connections": []}


@router.post("/", status_code=201)
async def create_connection(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    return {"message": "Connection created"}


@router.get("/{connection_id}")
async def get_connection(connection_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    return {"connection_id": connection_id}


@router.delete("/{connection_id}", status_code=204)
async def delete_connection(connection_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    return None


@router.post("/{connection_id}/test")
async def test_connection(connection_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    return {"status": "ok"}
