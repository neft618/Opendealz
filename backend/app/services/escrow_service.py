import uuid
import hashlib
import json
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog
from app.models.contract import Contract
from app.models.escrow import EscrowTransaction, EscrowTxType, EscrowTxStatus, InitiatedBy
from app.models.notification import NotificationType
from app.services.notification_service import create_notification
from app.core.config import settings


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


async def _write_audit(
    db: AsyncSession,
    entity_type: str,
    entity_id: uuid.UUID,
    action: str,
    tx_hash: str,
    user_id: Optional[uuid.UUID] = None,
    payload: Optional[dict] = None,
) -> None:
    log = AuditLog(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        user_id=user_id,
        payload=payload,
        tx_hash=tx_hash,
    )
    db.add(log)
    await db.flush()


async def lock_funds(
    db: AsyncSession,
    contract: Contract,
) -> EscrowTransaction:
    now = datetime.now(timezone.utc).isoformat()
    tx_hash = _sha256(f"{contract.id}:lock:{contract.total_amount}:{now}")

    tx = EscrowTransaction(
        contract_id=contract.id,
        type=EscrowTxType.lock,
        amount=contract.total_amount,
        status=EscrowTxStatus.confirmed,
        initiated_by=InitiatedBy.system,
        tx_hash=tx_hash,
        metadata={"action": "lock", "amount": float(contract.total_amount)},
    )
    db.add(tx)
    await db.flush()

    await _write_audit(
        db,
        entity_type="contract",
        entity_id=contract.id,
        action="escrow_lock",
        tx_hash=tx_hash,
        payload={"amount": float(contract.total_amount)},
    )
    return tx


async def release_funds(
    db: AsyncSession,
    contract: Contract,
) -> tuple[EscrowTransaction, EscrowTransaction]:
    now = datetime.now(timezone.utc).isoformat()
    executor_amount = float(contract.total_amount) - float(contract.platform_fee)
    fee_amount = float(contract.platform_fee)

    tx1_hash = _sha256(f"{contract.id}:release:{executor_amount}:{now}")
    tx2_hash = _sha256(f"{contract.id}:fee:{fee_amount}:{now}")

    tx1 = EscrowTransaction(
        contract_id=contract.id,
        type=EscrowTxType.release,
        amount=executor_amount,
        status=EscrowTxStatus.confirmed,
        initiated_by=InitiatedBy.customer,
        tx_hash=tx1_hash,
        metadata={"action": "release", "recipient": str(contract.executor_id)},
    )
    tx2 = EscrowTransaction(
        contract_id=contract.id,
        type=EscrowTxType.fee,
        amount=fee_amount,
        status=EscrowTxStatus.confirmed,
        initiated_by=InitiatedBy.system,
        tx_hash=tx2_hash,
        metadata={"action": "fee", "platform_fee": fee_amount},
    )
    db.add(tx1)
    db.add(tx2)
    await db.flush()

    await _write_audit(
        db,
        entity_type="contract",
        entity_id=contract.id,
        action="escrow_release",
        tx_hash=tx1_hash,
        payload={"executor_amount": executor_amount, "fee_amount": fee_amount},
    )
    return tx1, tx2


async def refund_funds(
    db: AsyncSession,
    contract: Contract,
) -> EscrowTransaction:
    now = datetime.now(timezone.utc).isoformat()
    tx_hash = _sha256(f"{contract.id}:refund:{contract.total_amount}:{now}")

    tx = EscrowTransaction(
        contract_id=contract.id,
        type=EscrowTxType.refund,
        amount=float(contract.total_amount),
        status=EscrowTxStatus.confirmed,
        initiated_by=InitiatedBy.system,
        tx_hash=tx_hash,
        metadata={"action": "refund", "recipient": str(contract.customer_id)},
    )
    db.add(tx)
    await db.flush()

    await _write_audit(
        db,
        entity_type="contract",
        entity_id=contract.id,
        action="escrow_refund",
        tx_hash=tx_hash,
        payload={"amount": float(contract.total_amount)},
    )
    return tx


async def release_shared(
    db: AsyncSession,
    contract: Contract,
) -> tuple[EscrowTransaction, EscrowTransaction]:
    """Split funds 50/50 between customer and executor."""
    now = datetime.now(timezone.utc).isoformat()
    half = float(contract.total_amount) / 2.0

    hash1 = _sha256(f"{contract.id}:release_shared_executor:{half}:{now}")
    hash2 = _sha256(f"{contract.id}:release_shared_customer:{half}:{now}")

    tx1 = EscrowTransaction(
        contract_id=contract.id,
        type=EscrowTxType.release,
        amount=half,
        status=EscrowTxStatus.confirmed,
        initiated_by=InitiatedBy.shared,
        tx_hash=hash1,
        metadata={"action": "shared_release_executor"},
    )
    tx2 = EscrowTransaction(
        contract_id=contract.id,
        type=EscrowTxType.refund,
        amount=half,
        status=EscrowTxStatus.confirmed,
        initiated_by=InitiatedBy.shared,
        tx_hash=hash2,
        metadata={"action": "shared_release_customer"},
    )
    db.add(tx1)
    db.add(tx2)
    await db.flush()

    shared_hash = _sha256(f"{contract.id}:shared_split:{float(contract.total_amount)}:{now}")
    await _write_audit(
        db,
        entity_type="contract",
        entity_id=contract.id,
        action="escrow_shared_split",
        tx_hash=shared_hash,
        payload={"half_amount": half},
    )
    return tx1, tx2
