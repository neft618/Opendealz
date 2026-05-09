import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from app.models.review import Review


class ReviewOut(BaseModel):
    id: uuid.UUID
    contract_id: uuid.UUID
    author_id: uuid.UUID
    recipient_id: uuid.UUID
    rating: int
    comment: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
