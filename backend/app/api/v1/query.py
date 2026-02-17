"""Direct query execution (admin only)."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.dependencies import get_current_user

router = APIRouter()


@router.post("/execute")
async def execute_query(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    return {"results": []}
