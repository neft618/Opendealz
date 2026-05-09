import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from app.models.escrow import EscrowTxType, EscrowTxStatus, InitiatedBy


class EscrowTransactionOut(BaseModel):
    id: uuid.UUID
    contract_id: uuid.UUID
    type: EscrowTxType
    amount: float
    status: EscrowTxStatus
    initiated_by: InitiatedBy
    tx_hash: str
    metadata: Optional[dict] = Field(default=None, validation_alias="metadata_")
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
