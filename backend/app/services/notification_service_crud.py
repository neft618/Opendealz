import uuid
from typing import List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.notification import Notification


async def get_notifications(
    db: AsyncSession, user: User, skip: int = 0, limit: int = 30
) -> List[Notification]:
    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == user.id)
        .order_by(Notification.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_unread_count(db: AsyncSession, user: User) -> int:
    result = await db.execute(
        select(func.count(Notification.id)).where(
            Notification.user_id == user.id,
            Notification.is_read == False,
        )
    )
    return result.scalar() or 0


async def mark_read(db: AsyncSession, user: User, notification_id: uuid.UUID) -> Notification:
    from fastapi import HTTPException
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user.id,
        )
    )
    n = result.scalar_one_or_none()
    if not n:
        raise HTTPException(status_code=404, detail="Notification not found")
    n.is_read = True
    await db.commit()
    await db.refresh(n)
    return n


async def mark_all_read(db: AsyncSession, user: User) -> None:
    result = await db.execute(
        select(Notification).where(
            Notification.user_id == user.id,
            Notification.is_read == False,
        )
    )
    for n in result.scalars().all():
        n.is_read = True
    await db.commit()
