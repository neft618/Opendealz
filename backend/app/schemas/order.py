import uuid
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field

from app.models.order import OrderStatus, ApplicationStatus


class OrderCreate(BaseModel):
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    budget: float = Field(..., gt=0)
    deadline: date


class OrderUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    budget: Optional[float] = Field(None, gt=0)
    deadline: Optional[date] = None
    status: Optional[OrderStatus] = None


class OrderOut(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    status: OrderStatus
    budget: float
    deadline: date
    customer_id: uuid.UUID
    executor_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ApplicationCreate(BaseModel):
    cover_letter: str = Field(..., min_length=1)
    proposed_price: float = Field(..., gt=0)


class ApplicationOut(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    executor_id: uuid.UUID
    cover_letter: str
    proposed_price: float
    status: ApplicationStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
