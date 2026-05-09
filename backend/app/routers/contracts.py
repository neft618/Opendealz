import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, UploadFile, File, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.contract import (
    ContractOut, ContractUpdate, ClauseUpdate, MilestoneCreate, MilestoneUpdate,
    MilestoneOut, DeliverableOut, ReviewCreate
)
from app.schemas.review import ReviewOut
from app.services import contract_service

router = APIRouter(prefix="/api/v1/contracts", tags=["contracts"])


@router.get("/{contract_id}", response_model=ContractOut)
async def get_contract(
    contract_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    return await contract_service.get_contract(db, contract_id, user)


@router.patch("/{contract_id}", response_model=ContractOut)
async def update_contract(
    contract_id: uuid.UUID,
    data: ContractUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    return await contract_service.update_contract(db, contract_id, user, data)


@router.patch("/{contract_id}/clauses", response_model=ContractOut)
async def update_clauses(
    contract_id: uuid.UUID,
    updates: List[ClauseUpdate],
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    return await contract_service.update_clauses(db, contract_id, user, updates)


@router.post("/{contract_id}/sign", response_model=ContractOut)
async def sign_contract(
    contract_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    return await contract_service.sign_contract(db, contract_id, user)


@router.post("/{contract_id}/milestones", response_model=MilestoneOut, status_code=201)
async def add_milestone(
    contract_id: uuid.UUID,
    data: MilestoneCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    return await contract_service.add_milestone(db, contract_id, user, data)


@router.patch("/{contract_id}/milestones/{mid}", response_model=MilestoneOut)
async def update_milestone(
    contract_id: uuid.UUID,
    mid: uuid.UUID,
    data: MilestoneUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    return await contract_service.update_milestone(db, contract_id, mid, user, data)


@router.post("/{contract_id}/deliverables", response_model=DeliverableOut, status_code=201)
async def upload_deliverable(
    contract_id: uuid.UUID,
    description: str = Form(...),
    milestone_id: Optional[uuid.UUID] = Form(None),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    return await contract_service.upload_deliverable(
        db, contract_id, user, file, description, milestone_id
    )


@router.get("/{contract_id}/deliverables/{did}/download")
async def download_deliverable(
    contract_id: uuid.UUID,
    did: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    url = await contract_service.get_deliverable_download_url(db, contract_id, did, user)
    return RedirectResponse(url=url)


@router.post("/{contract_id}/accept", response_model=ContractOut)
async def accept_contract(
    contract_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    return await contract_service.accept_contract(db, contract_id, user)


@router.post("/{contract_id}/reject", response_model=ContractOut)
async def reject_contract(
    contract_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    return await contract_service.reject_contract(db, contract_id, user)


@router.post("/{contract_id}/reviews", response_model=ReviewOut, status_code=201)
async def create_review(
    contract_id: uuid.UUID,
    data: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    return await contract_service.create_review(db, contract_id, user, data)
