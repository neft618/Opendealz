import uuid
import enum
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, Numeric, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class EscrowTxType(str, enum.Enum):
    lock = "lock"
    release = "release"
    refund = "refund"
    fee = "fee"


class EscrowTxStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    failed = "failed"


class InitiatedBy(str, enum.Enum):
    customer = "customer"
    executor = "executor"
    shared = "shared"
    system = "system"


class EscrowTransaction(Base):
    __tablename__ = "escrow_transactions"

    contract_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[EscrowTxType] = mapped_column(
        SAEnum(EscrowTxType, name="escrow_tx_type", create_type=True), nullable=False
    )
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[EscrowTxStatus] = mapped_column(
        SAEnum(EscrowTxStatus, name="escrow_tx_status", create_type=True),
        default=EscrowTxStatus.pending,
        nullable=False,
    )
    initiated_by: Mapped[InitiatedBy] = mapped_column(
        SAEnum(InitiatedBy, name="initiated_by", create_type=True), nullable=False
    )
    tx_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONB, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    contract: Mapped["Contract"] = relationship("Contract", back_populates="escrow_transactions")

    def __repr__(self) -> str:
        return f"<EscrowTransaction id={self.id} type={self.type} amount={self.amount}>"
