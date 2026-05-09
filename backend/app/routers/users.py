import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.user import UserOut, UserPublicOut, ProfileOut, PortfolioOut, RoleSwitchRequest, ReviewOut, ProfileUpdate
from app.services import user_service

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("/{user_id}", response_model=UserPublicOut)
async def get_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    return await user_service.get_user_public(db, user_id)


@router.patch("/me/profile", response_model=ProfileOut)
async def update_profile(
    data: ProfileUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    return await user_service.update_profile(db, user, data)


@router.patch("/me/role", response_model=UserOut)
async def switch_role(
    data: RoleSwitchRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    return await user_service.switch_role(db, user, data)


@router.post("/me/portfolio", response_model=PortfolioOut, status_code=201)
async def add_portfolio(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    return await user_service.add_portfolio(db, user, title, description, file)


@router.delete("/me/portfolio/{portfolio_id}", status_code=204)
async def delete_portfolio(
    portfolio_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    await user_service.delete_portfolio(db, user, portfolio_id)


@router.get("/{user_id}/reviews", response_model=List[ReviewOut])
async def get_reviews(
    user_id: uuid.UUID,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    return await user_service.get_user_reviews(db, user_id, skip, limit)
