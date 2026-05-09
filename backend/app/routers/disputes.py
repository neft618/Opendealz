import uuid
from typing import Optional

from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.models.dispute import DisputeStatus
from app.schemas.dispute import (
    DisputeCreate, DisputeOut, DisputeMessageCreate, DisputeMessageOut,
    DisputeStatusUpdate, DisputeResolveRequest
)
from app.services import dispute_service

router = APIRouter(prefix="/api/v1/disputes", tags=["disputes"])


@router.post("", response_model=DisputeOut, status_code=201)
async def create_dispute(
    data: DisputeCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    return await dispute_service.create_dispute(db, user, data)


@router.get("/{dispute_id}", response_model=DisputeOut)
async def get_dispute(
    dispute_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    return await dispute_service.get_dispute(db, dispute_id, user)


@router.post("/{dispute_id}/messages", response_model=DisputeMessageOut, status_code=201)
async def add_message(
    dispute_id: uuid.UUID,
    content: str,
    file: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    data = DisputeMessageCreate(content=content)
    return await dispute_service.add_dispute_message(db, dispute_id, user, data, file)


@router.patch("/{dispute_id}/status", response_model=DisputeOut)
async def update_dispute_status(
    dispute_id: uuid.UUID,
    data: DisputeStatusUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    return await dispute_service.update_dispute_status(db, dispute_id, user, data.status)


@router.post("/{dispute_id}/resolve", response_model=DisputeOut)
async def resolve_dispute(
    dispute_id: uuid.UUID,
    data: DisputeResolveRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    return await dispute_service.resolve_dispute(db, dispute_id, user, data)
