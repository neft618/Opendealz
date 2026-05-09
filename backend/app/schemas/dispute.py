import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

from app.models.dispute import DisputeStatus, DisputeResolution


class DisputeCreate(BaseModel):
    contract_id: uuid.UUID
    description: Optional[str] = None


class DisputeOut(BaseModel):
    id: uuid.UUID
    contract_id: uuid.UUID
    initiated_by_id: uuid.UUID
    description: Optional[str] = None
    status: DisputeStatus
    resolution: Optional[DisputeResolution] = None
    resolution_comment: Optional[str] = None
    resolved_by_id: Optional[uuid.UUID] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DisputeMessageCreate(BaseModel):
    content: str


class DisputeMessageOut(BaseModel):
    id: uuid.UUID
    dispute_id: uuid.UUID
    author_id: uuid.UUID
    content: str
    file_url: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DisputeStatusUpdate(BaseModel):
    status: DisputeStatus


class DisputeResolveRequest(BaseModel):
    resolution: DisputeResolution
    resolution_comment: Optional[str] = None
