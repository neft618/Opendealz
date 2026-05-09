import uuid
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel

from app.models.user import UserRole


class AdminUserOut(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    role: UserRole
    is_verified: bool
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminMetrics(BaseModel):
    total_users: int
    total_orders: int
    total_contracts: int
    total_disputes: int
    total_escrow_locked: float
    contracts_by_status: dict[str, int]
    disputes_last_30_days: int


class AuditLogOut(BaseModel):
    id: uuid.UUID
    entity_type: str
    entity_id: uuid.UUID
    action: str
    user_id: Optional[uuid.UUID] = None
    payload: Optional[Any] = None
    tx_hash: str
    ip_address: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
