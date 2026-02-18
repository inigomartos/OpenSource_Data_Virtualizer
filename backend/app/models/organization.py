"""Organization model — multi-tenancy root."""

from datetime import datetime, timezone
from sqlalchemy import String, Integer, BigInteger, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

# Default monthly token budgets per plan
PLAN_TOKEN_BUDGETS = {
    "free": 500_000,
    "starter": 2_000_000,
    "pro": 10_000_000,
    "enterprise": 50_000_000,
}


class Organization(BaseModel):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    plan: Mapped[str] = mapped_column(String(50), default="free")
    max_connections: Mapped[int] = mapped_column(Integer, default=5)
    max_users: Mapped[int] = mapped_column(Integer, default=10)

    # Token budgeting
    token_budget_monthly: Mapped[int] = mapped_column(
        BigInteger, default=PLAN_TOKEN_BUDGETS["free"], nullable=False,
    )
    token_usage_current: Mapped[int] = mapped_column(
        BigInteger, default=0, nullable=False,
    )
    budget_reset_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc).replace(
            day=1, hour=0, minute=0, second=0, microsecond=0,
        ),
        nullable=False,
    )

    # Relationships
    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    connections = relationship("Connection", back_populates="organization", cascade="all, delete-orphan")
    dashboards = relationship("Dashboard", back_populates="organization", cascade="all, delete-orphan")
    saved_queries = relationship("SavedQuery", back_populates="organization", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="organization", cascade="all, delete-orphan")
