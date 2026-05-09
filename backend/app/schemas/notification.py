import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from app.models.notification import NotificationType


class NotificationOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    type: NotificationType
    title: str
    message: str
    is_read: bool
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UnreadCountOut(BaseModel):
    count: int
