import uuid
from datetime import datetime, timedelta, timezone
from typing import List

from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.models.order import Order
from app.models.contract import Contract, ContractStatus
from app.models.dispute import Dispute
from app.models.escrow import EscrowTransaction, EscrowTxType
from app.models.audit import AuditLog


async def list_admin_users(
    db: AsyncSession,
    search: str = "",
    skip: int = 0,
    limit: int = 20,
) -> List[User]:
    query = select(User)
    if search:
        query = query.where(
            User.email.ilike(f"%{search}%") | User.full_name.ilike(f"%{search}%")
        )
    result = await db.execute(query.offset(skip).limit(limit))
    return list(result.scalars().all())


async def verify_user(db: AsyncSession, user_id: uuid.UUID) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_verified = True
    await db.commit()
    await db.refresh(user)
    return user


async def deactivate_user(db: AsyncSession, user_id: uuid.UUID) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False
    await db.commit()
    await db.refresh(user)
    return user


async def get_metrics(db: AsyncSession) -> dict:
    total_users = (await db.execute(select(func.count(User.id)))).scalar() or 0
    total_orders = (await db.execute(select(func.count(Order.id)))).scalar() or 0
    total_contracts = (await db.execute(select(func.count(Contract.id)))).scalar() or 0
    total_disputes = (await db.execute(select(func.count(Dispute.id)))).scalar() or 0

    locked_result = await db.execute(
        select(func.sum(EscrowTransaction.amount)).where(
            EscrowTransaction.type == EscrowTxType.lock
        )
    )
    total_escrow_locked = float(locked_result.scalar() or 0)

    # Contracts by status
    status_counts = {}
    for s in ContractStatus:
        cnt = (await db.execute(
            select(func.count(Contract.id)).where(Contract.status == s)
        )).scalar() or 0
        status_counts[s.value] = cnt

    # Disputes last 30 days
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    disputes_30 = (await db.execute(
        select(func.count(Dispute.id)).where(Dispute.created_at >= thirty_days_ago)
    )).scalar() or 0

    return {
        "total_users": total_users,
        "total_orders": total_orders,
        "total_contracts": total_contracts,
        "total_disputes": total_disputes,
        "total_escrow_locked": total_escrow_locked,
        "contracts_by_status": status_counts,
        "disputes_last_30_days": disputes_30,
    }


async def get_audit_log(
    db: AsyncSession, skip: int = 0, limit: int = 50
) -> List[AuditLog]:
    result = await db.execute(
        select(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())
