import uuid
import enum
from datetime import datetime, timezone, date
from typing import Optional, List

from sqlalchemy import String, Text, Numeric, Date, DateTime, ForeignKey, Enum as SAEnum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class OrderStatus(str, enum.Enum):
    open = "open"
    in_progress = "in_progress"
    closed = "closed"
    cancelled = "cancelled"


class ApplicationStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"


class Order(Base):
    __tablename__ = "orders"

    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[OrderStatus] = mapped_column(
        SAEnum(OrderStatus, name="order_status", create_type=True),
        default=OrderStatus.open,
        nullable=False,
    )
    budget: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    deadline: Mapped[date] = mapped_column(Date, nullable=False)
    customer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    executor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    customer: Mapped["User"] = relationship(
        "User", foreign_keys=[customer_id], back_populates="orders"
    )
    executor: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[executor_id], back_populates="executor_orders"
    )
    applications: Mapped[List["Application"]] = relationship(
        "Application", back_populates="order", cascade="all, delete-orphan"
    )
    contract: Mapped[Optional["Contract"]] = relationship(
        "Contract", back_populates="order", uselist=False
    )

    def __repr__(self) -> str:
        return f"<Order id={self.id} title={self.title}>"


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (
        UniqueConstraint("order_id", "executor_id", name="uq_application_order_executor"),
    )

    order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    executor_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    cover_letter: Mapped[str] = mapped_column(Text, nullable=False)
    proposed_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[ApplicationStatus] = mapped_column(
        SAEnum(ApplicationStatus, name="application_status", create_type=True),
        default=ApplicationStatus.pending,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    order: Mapped["Order"] = relationship("Order", back_populates="applications")
    executor: Mapped["User"] = relationship(
        "User", foreign_keys=[executor_id], back_populates="applications"
    )

    def __repr__(self) -> str:
        return f"<Application id={self.id} order_id={self.order_id}>"
