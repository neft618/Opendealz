import uuid
from typing import Optional, List

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User, Profile, Portfolio
from app.models.review import Review
from app.models.contract import Contract
from app.schemas.user import ProfileUpdate, RoleSwitchRequest
from app.core.storage import upload_file


ALLOWED_EXTENSIONS = {".pdf", ".docx", ".zip", ".png", ".jpg", ".jpeg"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


async def get_user_public(db: AsyncSession, user_id: uuid.UUID) -> dict:
    result = await db.execute(
        select(User)
        .options(
            selectinload(User.profile).selectinload(Profile.portfolios)
        )
        .where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Compute average rating
    rating_result = await db.execute(
        select(func.avg(Review.rating)).where(Review.recipient_id == user_id)
    )
    avg_rating = rating_result.scalar()

    # Count reviews
    reviews_count_result = await db.execute(
        select(func.count(Review.id)).where(Review.recipient_id == user_id)
    )
    reviews_count = reviews_count_result.scalar() or 0

    # Count contracts
    contracts_count_result = await db.execute(
        select(func.count(Contract.id)).where(
            (Contract.customer_id == user_id) | (Contract.executor_id == user_id)
        )
    )
    contracts_count = contracts_count_result.scalar() or 0

    portfolios = user.profile.portfolios if user.profile else []

    return {
        "id": user.id,
        "full_name": user.full_name,
        "role": user.role,
        "is_verified": user.is_verified,
        "created_at": user.created_at,
        "profile": user.profile,
        "portfolios": portfolios,
        "rating": float(avg_rating) if avg_rating else None,
        "reviews_count": reviews_count,
        "contracts_count": contracts_count,
    }


async def update_profile(
    db: AsyncSession,
    user: User,
    data: ProfileUpdate,
) -> Profile:
    result = await db.execute(
        select(Profile).where(Profile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        profile = Profile(user_id=user.id)
        db.add(profile)

    for field, val in data.model_dump(exclude_unset=True).items():
        setattr(profile, field, val)

    await db.commit()
    await db.refresh(profile)
    return profile


async def switch_role(db: AsyncSession, user: User, data: RoleSwitchRequest) -> User:
    from app.models.user import UserRole
    if data.role == UserRole.admin:
        raise HTTPException(status_code=403, detail="Cannot switch to admin role")
    user.role = data.role
    await db.commit()
    await db.refresh(user)
    return user


async def add_portfolio(
    db: AsyncSession,
    user: User,
    title: str,
    description: Optional[str],
    file: UploadFile,
) -> Portfolio:
    import os
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type {ext} not allowed")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File exceeds 10MB limit")

    result = await db.execute(select(Profile).where(Profile.user_id == user.id))
    profile = result.scalar_one_or_none()
    if not profile:
        profile = Profile(user_id=user.id)
        db.add(profile)
        await db.flush()

    path = f"{user.id}/{uuid.uuid4()}{ext}"
    from app.core.config import settings
    file_url = await upload_file(settings.SUPABASE_BUCKET_PORTFOLIOS, path, content, file.content_type or "application/octet-stream")

    portfolio = Portfolio(
        profile_id=profile.id,
        title=title,
        description=description,
        file_url=file_url,
    )
    db.add(portfolio)
    await db.commit()
    await db.refresh(portfolio)
    return portfolio


async def delete_portfolio(
    db: AsyncSession,
    user: User,
    portfolio_id: uuid.UUID,
) -> None:
    result = await db.execute(
        select(Portfolio)
        .join(Profile)
        .where(Portfolio.id == portfolio_id, Profile.user_id == user.id)
    )
    portfolio = result.scalar_one_or_none()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    await db.delete(portfolio)
    await db.commit()


async def get_user_reviews(
    db: AsyncSession,
    user_id: uuid.UUID,
    skip: int = 0,
    limit: int = 20,
) -> List[Review]:
    result = await db.execute(
        select(Review)
        .where(Review.recipient_id == user_id)
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())
