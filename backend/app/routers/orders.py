import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.models.order import OrderStatus
from app.schemas.order import OrderCreate, OrderUpdate, OrderOut, ApplicationCreate, ApplicationOut
from app.schemas.contract import ContractOut
from app.services import order_service

router = APIRouter(prefix="/api/v1/orders", tags=["orders"])


@router.post("", response_model=OrderOut, status_code=201)
async def create_order(
    data: OrderCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    return await order_service.create_order(db, user, data)


@router.get("", response_model=List[OrderOut])
async def list_orders(
    search: Optional[str] = Query(None),
    status: Optional[OrderStatus] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    return await order_service.list_orders(db, search, status, skip, limit)


@router.get("/{order_id}", response_model=OrderOut)
async def get_order(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    return await order_service.get_order(db, order_id)


@router.patch("/{order_id}", response_model=OrderOut)
async def update_order(
    order_id: uuid.UUID,
    data: OrderUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    return await order_service.update_order(db, user, order_id, data)


@router.delete("/{order_id}", status_code=204)
async def delete_order(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    await order_service.delete_order(db, user, order_id)


@router.post("/{order_id}/applications", response_model=ApplicationOut, status_code=201)
async def apply_to_order(
    order_id: uuid.UUID,
    data: ApplicationCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    return await order_service.apply_to_order(db, user, order_id, data)


@router.get("/{order_id}/applications", response_model=List[ApplicationOut])
async def list_applications(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    return await order_service.get_order_applications(db, user, order_id)


@router.post("/{order_id}/applications/{app_id}/accept", response_model=ContractOut)
async def accept_application(
    order_id: uuid.UUID,
    app_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    return await order_service.accept_application(db, user, order_id, app_id)
