import uuid
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.notification import NotificationOut, UnreadCountOut
from app.services import notification_service_crud as svc

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


@router.get("", response_model=List[NotificationOut])
async def list_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(30, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    return await svc.get_notifications(db, user, skip, limit)


@router.get("/unread-count", response_model=UnreadCountOut)
async def unread_count(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    count = await svc.get_unread_count(db, user)
    return {"count": count}


@router.patch("/read-all", status_code=204)
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    await svc.mark_all_read(db, user)


@router.patch("/{notification_id}/read", response_model=NotificationOut)
async def mark_read(
    notification_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    return await svc.mark_read(db, user, notification_id)
