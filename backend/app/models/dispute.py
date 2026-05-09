import uuid
import enum
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import String, Text, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class DisputeStatus(str, enum.Enum):
    open = "open"
    under_review = "under_review"
    resolved = "resolved"


class DisputeResolution(str, enum.Enum):
    executor = "executor"
    customer = "customer"
    shared = "shared"


class Dispute(Base):
    __tablename__ = "disputes"

    contract_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("contracts.id", ondelete="RESTRICT"), nullable=False
    )
    initiated_by_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[DisputeStatus] = mapped_column(
        SAEnum(DisputeStatus, name="dispute_status", create_type=True),
        default=DisputeStatus.open,
        nullable=False,
    )
    resolution: Mapped[Optional[DisputeResolution]] = mapped_column(
        SAEnum(DisputeResolution, name="dispute_resolution", create_type=True), nullable=True
    )
    resolution_comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    contract: Mapped["Contract"] = relationship("Contract", back_populates="disputes")
    initiated_by: Mapped["User"] = relationship(
        "User", foreign_keys=[initiated_by_id], back_populates="disputes_initiated"
    )
    resolved_by: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[resolved_by_id], back_populates="disputes_resolved"
    )
    messages: Mapped[List["DisputeMessage"]] = relationship(
        "DisputeMessage", back_populates="dispute", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Dispute id={self.id} status={self.status}>"


class DisputeMessage(Base):
    __tablename__ = "dispute_messages"

    dispute_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("disputes.id", ondelete="CASCADE"), nullable=False
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    file_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    dispute: Mapped["Dispute"] = relationship("Dispute", back_populates="messages")
    author: Mapped["User"] = relationship("User", back_populates="dispute_messages")

    def __repr__(self) -> str:
        return f"<DisputeMessage id={self.id} dispute_id={self.dispute_id}>"
