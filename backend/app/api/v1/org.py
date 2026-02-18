"""Organization management endpoints (budget, settings)."""

from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import raise_forbidden
from app.dependencies import get_current_user
from app.models.user import User
from app.services.token_budget_service import TokenBudgetService

router = APIRouter()


class BudgetUpdateRequest(BaseModel):
    token_budget_monthly: Optional[int] = Field(
        None, ge=0, description="Monthly token budget (0 = unlimited)"
    )


@router.get("/budget")
async def get_budget(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get the current organization's token budget status."""
    service = TokenBudgetService()
    return await service.get_budget_status(str(user.org_id), db)


@router.put("/budget")
async def update_budget(
    payload: BudgetUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update the organization's token budget. Admin only."""
    if user.role != "admin":
        raise_forbidden("Only admins can update the token budget")

    from sqlalchemy import select
    from app.models.organization import Organization

    result = await db.execute(
        select(Organization).where(Organization.id == user.org_id)
    )
    org = result.scalar_one_or_none()
    if not org:
        raise_forbidden("Organization not found")

    if payload.token_budget_monthly is not None:
        org.token_budget_monthly = payload.token_budget_monthly

    await db.flush()

    service = TokenBudgetService()
    return await service.get_budget_status(str(user.org_id), db)
