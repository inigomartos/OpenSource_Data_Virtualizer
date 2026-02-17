"""Dashboard CRUD endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.dependencies import get_current_user

router = APIRouter()


@router.get("/")
async def list_dashboards(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    return {"dashboards": []}


@router.post("/", status_code=201)
async def create_dashboard(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    return {"message": "Dashboard created"}


@router.get("/{dashboard_id}")
async def get_dashboard(dashboard_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    return {"dashboard_id": dashboard_id}


@router.delete("/{dashboard_id}", status_code=204)
async def delete_dashboard(dashboard_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    return None
