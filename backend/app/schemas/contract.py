import uuid
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field

from app.models.contract import ContractStatus, PaymentType, ClauseType, MilestoneStatus


class ClauseOut(BaseModel):
    id: uuid.UUID
    contract_id: uuid.UUID
    clause_type: ClauseType
    content: str
    position: int
    is_mandatory: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ClauseUpdate(BaseModel):
    id: uuid.UUID
    content: Optional[str] = None
    position: Optional[int] = None


class MilestoneCreate(BaseModel):
    title: str = Field(..., min_length=1)
    description: Optional[str] = None
    amount: float = Field(..., gt=0)
    deadline: date
    position: int


class MilestoneUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[float] = Field(None, gt=0)
    deadline: Optional[date] = None
    status: Optional[MilestoneStatus] = None
    position: Optional[int] = None


class MilestoneOut(BaseModel):
    id: uuid.UUID
    contract_id: uuid.UUID
    title: str
    description: Optional[str] = None
    amount: float
    deadline: date
    status: MilestoneStatus
    position: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DeliverableOut(BaseModel):
    id: uuid.UUID
    contract_id: uuid.UUID
    milestone_id: Optional[uuid.UUID] = None
    file_url: str
    file_name: str
    file_size: int
    description: str
    submitted_by_id: uuid.UUID
    submitted_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ContractOut(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    customer_id: uuid.UUID
    executor_id: uuid.UUID
    status: ContractStatus
    total_amount: float
    platform_fee: float
    payment_type: PaymentType
    review_period_days: int
    contract_hash: Optional[str] = None
    signed_at: Optional[datetime] = None
    customer_signed_at: Optional[datetime] = None
    executor_signed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    clauses: List[ClauseOut] = []
    milestones: List[MilestoneOut] = []
    deliverables: List[DeliverableOut] = []

    model_config = {"from_attributes": True}


class ContractUpdate(BaseModel):
    total_amount: Optional[float] = Field(None, gt=0)
    payment_type: Optional[PaymentType] = None
    review_period_days: Optional[int] = Field(None, ge=1)


class ReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None
