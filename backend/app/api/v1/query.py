"""Direct query execution (admin only)."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter()


@router.post("/execute")
async def execute_query(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    return {"results": []}


@router.get("/saved")
async def list_saved_queries(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from app.models.saved_query import SavedQuery
    result = await db.execute(
        select(SavedQuery)
        .where(SavedQuery.org_id == user.org_id)
        .order_by(SavedQuery.created_at.desc())
    )
    queries = result.scalars().all()
    return {"data": [{"id": str(q.id), "name": q.name, "query_sql": q.query_sql, "created_at": str(q.created_at)} for q in queries], "count": len(queries)}
