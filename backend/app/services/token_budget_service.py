"""Per-org token budget enforcement and tracking."""

import calendar
from datetime import datetime, timezone, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Organization, PLAN_TOKEN_BUDGETS
from loguru import logger


class TokenBudgetExceeded(Exception):
    """Raised when an org has exhausted its monthly token budget."""

    def __init__(self, org_id: str, used: int, budget: int):
        self.org_id = org_id
        self.used = used
        self.budget = budget
        super().__init__(
            f"Token budget exceeded for org {org_id}: "
            f"{used:,}/{budget:,} tokens used"
        )


class TokenBudgetService:
    """Checks and records per-org token usage against monthly budgets."""

    async def check_budget(self, org_id: str, db: AsyncSession) -> None:
        """Raise TokenBudgetExceeded if the org is over budget.

        Also resets the counter if the billing period has rolled over.
        """
        org = await self._get_org(org_id, db)
        if not org:
            return  # Fail-open if org not found

        await self._reset_if_needed(org, db)

        if org.token_usage_current >= org.token_budget_monthly:
            raise TokenBudgetExceeded(
                org_id=str(org.id),
                used=org.token_usage_current,
                budget=org.token_budget_monthly,
            )

    async def record_usage(
        self,
        org_id: str,
        input_tokens: int,
        output_tokens: int,
        db: AsyncSession,
    ) -> None:
        """Add token usage to the org's running total."""
        org = await self._get_org(org_id, db)
        if not org:
            return

        total = input_tokens + output_tokens
        org.token_usage_current = Organization.token_usage_current + total
        await db.flush()
        logger.debug(
            f"Recorded {total:,} tokens for org {org_id} "
            f"(new total: {org.token_usage_current:,})"
        )

    async def get_budget_status(
        self, org_id: str, db: AsyncSession
    ) -> dict:
        """Return current budget info for an organization."""
        org = await self._get_org(org_id, db)
        if not org:
            return {"error": "Organization not found"}

        await self._reset_if_needed(org, db)

        return {
            "org_id": str(org.id),
            "plan": org.plan,
            "token_budget_monthly": org.token_budget_monthly,
            "token_usage_current": org.token_usage_current,
            "tokens_remaining": max(
                0, org.token_budget_monthly - org.token_usage_current
            ),
            "usage_percent": round(
                (org.token_usage_current / org.token_budget_monthly) * 100, 1
            )
            if org.token_budget_monthly > 0
            else 0,
            "budget_reset_at": org.budget_reset_at.isoformat()
            if org.budget_reset_at
            else None,
        }

    # ── Internal ────────────────────────────────────────────────────

    async def _get_org(
        self, org_id: str, db: AsyncSession
    ) -> Organization | None:
        result = await db.execute(
            select(Organization).where(Organization.id == org_id)
        )
        return result.scalar_one_or_none()

    async def _reset_if_needed(
        self, org: Organization, db: AsyncSession
    ) -> None:
        """Reset token counter if the billing period has rolled over."""
        now = datetime.now(timezone.utc)
        if org.budget_reset_at and now >= org.budget_reset_at:
            org.token_usage_current = 0
            # Next reset = first day of next month (no dateutil needed)
            year = org.budget_reset_at.year
            month = org.budget_reset_at.month
            if month == 12:
                year += 1
                month = 1
            else:
                month += 1
            next_reset = datetime(
                year, month, 1, tzinfo=timezone.utc,
            )
            org.budget_reset_at = next_reset
            await db.flush()
            logger.info(
                f"Reset token budget for org {org.id}, "
                f"next reset: {next_reset.isoformat()}"
            )
