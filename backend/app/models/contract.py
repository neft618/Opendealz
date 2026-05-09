import uuid
import enum
from datetime import datetime, timezone, date
from typing import Optional, List

from sqlalchemy import (
    String, Text, Numeric, Date, DateTime, Integer, Boolean,
    ForeignKey, Enum as SAEnum, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ContractStatus(str, enum.Enum):
    draft = "draft"
    signed = "signed"
    in_progress = "in_progress"
    completed = "completed"
    disputed = "disputed"
    cancelled = "cancelled"


class PaymentType(str, enum.Enum):
    fixed = "fixed"
    hourly = "hourly"
    milestone = "milestone"


class ClauseType(str, enum.Enum):
    subject_description = "subject_description"
    timeline = "timeline"
    payment_terms = "payment_terms"
    termination_conditions = "termination_conditions"
    result_review_period = "result_review_period"
    refund_policy = "refund_policy"
    platform_commission = "platform_commission"
    ip_rights = "ip_rights"
    confidentiality = "confidentiality"


class MilestoneStatus(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    approved = "approved"
    rejected = "rejected"


class Contract(Base):
    __tablename__ = "contracts"
    __table_args__ = (
        UniqueConstraint("order_id", name="uq_contracts_order_id"),
    )

    order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("orders.id", ondelete="RESTRICT"), nullable=False
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    executor_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[ContractStatus] = mapped_column(
        SAEnum(ContractStatus, name="contract_status", create_type=True),
        default=ContractStatus.draft,
        nullable=False,
    )
    total_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    platform_fee: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    payment_type: Mapped[PaymentType] = mapped_column(
        SAEnum(PaymentType, name="payment_type", create_type=True), nullable=False
    )
    review_period_days: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    contract_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    signed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    customer_signed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    executor_signed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    order: Mapped["Order"] = relationship("Order", back_populates="contract")
    customer: Mapped["User"] = relationship(
        "User", foreign_keys=[customer_id], back_populates="customer_contracts"
    )
    executor: Mapped["User"] = relationship(
        "User", foreign_keys=[executor_id], back_populates="executor_contracts"
    )
    clauses: Mapped[List["ContractClause"]] = relationship(
        "ContractClause", back_populates="contract", cascade="all, delete-orphan",
        order_by="ContractClause.position"
    )
    milestones: Mapped[List["Milestone"]] = relationship(
        "Milestone", back_populates="contract", cascade="all, delete-orphan",
        order_by="Milestone.position"
    )
    deliverables: Mapped[List["Deliverable"]] = relationship(
        "Deliverable", back_populates="contract", cascade="all, delete-orphan"
    )
    escrow_transactions: Mapped[List["EscrowTransaction"]] = relationship(
        "EscrowTransaction", back_populates="contract", cascade="all, delete-orphan"
    )
    disputes: Mapped[List["Dispute"]] = relationship(
        "Dispute", back_populates="contract"
    )
    reviews: Mapped[List["Review"]] = relationship(
        "Review", back_populates="contract"
    )

    def __repr__(self) -> str:
        return f"<Contract id={self.id} status={self.status}>"


class ContractClause(Base):
    __tablename__ = "contract_clauses"

    contract_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False
    )
    clause_type: Mapped[ClauseType] = mapped_column(
        SAEnum(ClauseType, name="clause_type", create_type=True), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    contract: Mapped["Contract"] = relationship("Contract", back_populates="clauses")

    def __repr__(self) -> str:
        return f"<ContractClause id={self.id} type={self.clause_type}>"


class Milestone(Base):
    __tablename__ = "milestones"

    contract_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    deadline: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[MilestoneStatus] = mapped_column(
        SAEnum(MilestoneStatus, name="milestone_status", create_type=True),
        default=MilestoneStatus.pending,
        nullable=False,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    contract: Mapped["Contract"] = relationship("Contract", back_populates="milestones")
    deliverables: Mapped[List["Deliverable"]] = relationship(
        "Deliverable", back_populates="milestone"
    )

    def __repr__(self) -> str:
        return f"<Milestone id={self.id} title={self.title}>"


class Deliverable(Base):
    __tablename__ = "deliverables"

    contract_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False
    )
    milestone_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("milestones.id", ondelete="SET NULL"), nullable=True
    )
    file_url: Mapped[str] = mapped_column(String, nullable=False)
    file_name: Mapped[str] = mapped_column(String, nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    submitted_by_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    contract: Mapped["Contract"] = relationship("Contract", back_populates="deliverables")
    milestone: Mapped[Optional["Milestone"]] = relationship("Milestone", back_populates="deliverables")
    submitted_by: Mapped["User"] = relationship("User", back_populates="deliverables_submitted")

    def __repr__(self) -> str:
        return f"<Deliverable id={self.id} file_name={self.file_name}>"
