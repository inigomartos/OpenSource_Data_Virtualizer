"""Alert CRUD endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.dependencies import get_current_user

router = APIRouter()


@router.get("/")
async def list_alerts(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    return {"alerts": []}


@router.post("/", status_code=201)
async def create_alert(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    return {"message": "Alert created"}


@router.delete("/{alert_id}", status_code=204)
async def delete_alert(alert_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    return None
