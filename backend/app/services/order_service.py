import uuid
from typing import Optional, List

from fastapi import HTTPException
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import Order, Application, OrderStatus, ApplicationStatus
from app.models.user import User
from app.models.contract import Contract, ContractClause, ClauseType, PaymentType
from app.schemas.order import OrderCreate, OrderUpdate, ApplicationCreate
from app.models.notification import NotificationType
from app.services.notification_service import create_notification
from app.core.config import settings


DEFAULT_CLAUSES = [
    ClauseType.subject_description,
    ClauseType.timeline,
    ClauseType.payment_terms,
    ClauseType.termination_conditions,
    ClauseType.result_review_period,
    ClauseType.refund_policy,
    ClauseType.platform_commission,
    ClauseType.ip_rights,
    ClauseType.confidentiality,
]


async def create_order(
    db: AsyncSession,
    user: User,
    data: OrderCreate,
) -> Order:
    order = Order(
        title=data.title,
        description=data.description,
        budget=data.budget,
        deadline=data.deadline,
        customer_id=user.id,
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)
    return order


async def list_orders(
    db: AsyncSession,
    search: Optional[str] = None,
    status: Optional[OrderStatus] = None,
    skip: int = 0,
    limit: int = 20,
) -> List[Order]:
    query = select(Order)
    if search:
        query = query.where(
            or_(Order.title.ilike(f"%{search}%"), Order.description.ilike(f"%{search}%"))
        )
    if status:
        query = query.where(Order.status == status)
    query = query.offset(skip).limit(limit).order_by(Order.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_order(db: AsyncSession, order_id: uuid.UUID) -> Order:
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.customer), selectinload(Order.applications))
        .where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


async def update_order(
    db: AsyncSession,
    user: User,
    order_id: uuid.UUID,
    data: OrderUpdate,
) -> Order:
    order = await get_order(db, order_id)
    if order.customer_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if order.status != OrderStatus.open:
        raise HTTPException(status_code=400, detail="Can only update open orders")
    for field, val in data.model_dump(exclude_unset=True).items():
        setattr(order, field, val)
    await db.commit()
    await db.refresh(order)
    return order


async def delete_order(
    db: AsyncSession,
    user: User,
    order_id: uuid.UUID,
) -> None:
    order = await get_order(db, order_id)
    if order.customer_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if order.status != OrderStatus.open:
        raise HTTPException(status_code=400, detail="Can only delete open orders")
    await db.delete(order)
    await db.commit()


async def apply_to_order(
    db: AsyncSession,
    user: User,
    order_id: uuid.UUID,
    data: ApplicationCreate,
) -> Application:
    order = await get_order(db, order_id)
    if order.status != OrderStatus.open:
        raise HTTPException(status_code=400, detail="Order is not open")
    if order.customer_id == user.id:
        raise HTTPException(status_code=400, detail="Cannot apply to your own order")

    existing = await db.execute(
        select(Application).where(
            Application.order_id == order_id,
            Application.executor_id == user.id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Already applied")

    app = Application(
        order_id=order_id,
        executor_id=user.id,
        cover_letter=data.cover_letter,
        proposed_price=data.proposed_price,
    )
    db.add(app)
    await db.flush()

    await create_notification(
        db, order.customer_id, NotificationType.contract,
        "New application received",
        f"You received a new application for order '{order.title}'.",
        related_entity_type="application",
        related_entity_id=app.id,
    )
    await db.commit()
    await db.refresh(app)
    return app


async def get_order_applications(
    db: AsyncSession, user: User, order_id: uuid.UUID
) -> List[Application]:
    order = await get_order(db, order_id)
    if order.customer_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    result = await db.execute(
        select(Application).where(Application.order_id == order_id)
    )
    return list(result.scalars().all())


async def accept_application(
    db: AsyncSession,
    user: User,
    order_id: uuid.UUID,
    app_id: uuid.UUID,
) -> Contract:
    order = await get_order(db, order_id)
    if order.customer_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if order.status != OrderStatus.open:
        raise HTTPException(status_code=400, detail="Order is not open")

    app_result = await db.execute(
        select(Application).where(Application.id == app_id, Application.order_id == order_id)
    )
    app = app_result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    if app.status != ApplicationStatus.pending:
        raise HTTPException(status_code=400, detail="Application already processed")

    # Accept this application, reject others
    app.status = ApplicationStatus.accepted
    other_apps = await db.execute(
        select(Application).where(
            Application.order_id == order_id,
            Application.id != app_id,
            Application.status == ApplicationStatus.pending,
        )
    )
    for other in other_apps.scalars().all():
        other.status = ApplicationStatus.rejected

    # Update order
    order.status = OrderStatus.in_progress
    order.executor_id = app.executor_id

    fee_amount = round(float(app.proposed_price) * settings.PLATFORM_FEE_PERCENT / 100, 2)

    # Create contract draft with default clauses
    contract = Contract(
        order_id=order_id,
        customer_id=user.id,
        executor_id=app.executor_id,
        total_amount=app.proposed_price,
        platform_fee=fee_amount,
        payment_type=PaymentType.fixed,
    )
    db.add(contract)
    await db.flush()

    for i, clause_type in enumerate(DEFAULT_CLAUSES):
        clause = ContractClause(
            contract_id=contract.id,
            clause_type=clause_type,
            content="",
            position=i,
            is_mandatory=True,
        )
        db.add(clause)

    await create_notification(
        db, app.executor_id, NotificationType.contract,
        "Application accepted",
        f"Your application for order '{order.title}' was accepted! A contract draft has been created.",
        related_entity_type="contract",
        related_entity_id=contract.id,
    )

    await db.commit()
    await db.refresh(contract)
    return contract
