import uuid
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import require_admin
from app.models.user import User
from app.schemas.admin import AdminUserOut, AdminMetrics, AuditLogOut
from app.schemas.contract import ContractOut
from app.schemas.dispute import DisputeOut
from app.services import admin_service
from app.services.contract_service import get_contract

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.get("/users", response_model=List[AdminUserOut])
async def list_users(
    search: str = Query(""),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await admin_service.list_admin_users(db, search, skip, limit)


@router.patch("/users/{user_id}/verify", response_model=AdminUserOut)
async def verify_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await admin_service.verify_user(db, user_id)


@router.patch("/users/{user_id}/deactivate", response_model=AdminUserOut)
async def deactivate_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await admin_service.deactivate_user(db, user_id)


@router.get("/metrics", response_model=AdminMetrics)
async def get_metrics(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await admin_service.get_metrics(db)


@router.get("/audit-log", response_model=List[AuditLogOut])
async def get_audit_log(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await admin_service.get_audit_log(db, skip, limit)


@router.get("/contracts", response_model=List[ContractOut])
async def list_contracts(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from app.models.contract import Contract
    result = await db.execute(
        select(Contract)
        .options(
            selectinload(Contract.clauses),
            selectinload(Contract.milestones),
            selectinload(Contract.deliverables),
            selectinload(Contract.escrow_transactions),
        )
        .offset(skip)
        .limit(limit)
        .order_by(Contract.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/disputes", response_model=List[DisputeOut])
async def list_disputes(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    from sqlalchemy import select
    from app.models.dispute import Dispute
    result = await db.execute(
        select(Dispute).offset(skip).limit(limit).order_by(Dispute.created_at.desc())
    )
    return list(result.scalars().all())
