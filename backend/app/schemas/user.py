import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr

from app.models.user import UserRole, Specialization


class ProfileBase(BaseModel):
    bio: Optional[str] = None
    skills: Optional[str] = None
    specialization: Optional[Specialization] = None


class ProfileUpdate(ProfileBase):
    pass


class PortfolioOut(BaseModel):
    id: uuid.UUID
    profile_id: uuid.UUID
    title: str
    description: Optional[str] = None
    file_url: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProfileOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    bio: Optional[str] = None
    skills: Optional[str] = None
    specialization: Optional[Specialization] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserOut(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: UserRole
    is_verified: bool
    is_active: bool
    wallet_address: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    profile: Optional[ProfileOut] = None

    model_config = {"from_attributes": True}


class UserPublicOut(BaseModel):
    id: uuid.UUID
    full_name: str
    role: UserRole
    is_verified: bool
    created_at: datetime
    profile: Optional[ProfileOut] = None
    portfolios: List[PortfolioOut] = []
    rating: Optional[float] = None
    reviews_count: int = 0
    contracts_count: int = 0

    model_config = {"from_attributes": True}


class RoleSwitchRequest(BaseModel):
    role: UserRole


class ReviewOut(BaseModel):
    id: uuid.UUID
    contract_id: uuid.UUID
    author_id: uuid.UUID
    recipient_id: uuid.UUID
    rating: int
    comment: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
