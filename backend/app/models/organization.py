"""Organization model — multi-tenancy root."""

from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Organization(BaseModel):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    plan: Mapped[str] = mapped_column(String(50), default="free")
    max_connections: Mapped[int] = mapped_column(Integer, default=5)
    max_users: Mapped[int] = mapped_column(Integer, default=10)

    # Relationships
    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    connections = relationship("Connection", back_populates="organization", cascade="all, delete-orphan")
    dashboards = relationship("Dashboard", back_populates="organization", cascade="all, delete-orphan")
    saved_queries = relationship("SavedQuery", back_populates="organization", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="organization", cascade="all, delete-orphan")
