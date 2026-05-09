import uuid
from typing import Optional, List

from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.dispute import Dispute, DisputeMessage, DisputeStatus, DisputeResolution
from app.models.contract import Contract, ContractStatus
from app.models.user import User
from app.models.notification import NotificationType
from app.schemas.dispute import DisputeCreate, DisputeMessageCreate, DisputeResolveRequest
from app.services import escrow_service, notification_service
from app.core.storage import upload_file
from app.core.config import settings


ALLOWED_EXTENSIONS = {".pdf", ".docx", ".zip", ".png", ".jpg", ".jpeg"}
MAX_FILE_SIZE = 10 * 1024 * 1024


async def create_dispute(
    db: AsyncSession, user: User, data: DisputeCreate
) -> Dispute:
    result = await db.execute(select(Contract).where(Contract.id == data.contract_id))
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    if contract.customer_id != user.id and contract.executor_id != user.id:
        raise HTTPException(status_code=403, detail="Not a party to this contract")
    if contract.status not in (ContractStatus.in_progress, ContractStatus.disputed):
        raise HTTPException(status_code=400, detail="Cannot open dispute in current contract status")

    dispute = Dispute(
        contract_id=data.contract_id,
        initiated_by_id=user.id,
        description=data.description,
        status=DisputeStatus.open,
    )
    db.add(dispute)
    await db.flush()

    # Notify the other party
    other_id = contract.executor_id if contract.customer_id == user.id else contract.customer_id
    await notification_service.create_notification(
        db, other_id, NotificationType.dispute,
        "Dispute opened",
        f"A dispute has been opened for your contract.",
        related_entity_type="dispute",
        related_entity_id=dispute.id,
    )

    await db.commit()
    await db.refresh(dispute)
    return dispute


async def get_dispute(
    db: AsyncSession, dispute_id: uuid.UUID, user: User
) -> Dispute:
    result = await db.execute(
        select(Dispute)
        .options(selectinload(Dispute.messages))
        .where(Dispute.id == dispute_id)
    )
    dispute = result.scalar_one_or_none()
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")

    # Check access
    contract_result = await db.execute(select(Contract).where(Contract.id == dispute.contract_id))
    contract = contract_result.scalar_one_or_none()
    if contract and contract.customer_id != user.id and contract.executor_id != user.id:
        if user.role.value != "admin":
            raise HTTPException(status_code=403, detail="Not authorized")

    return dispute


async def add_dispute_message(
    db: AsyncSession,
    dispute_id: uuid.UUID,
    user: User,
    data: DisputeMessageCreate,
    file: Optional[UploadFile] = None,
) -> DisputeMessage:
    import os
    dispute = await get_dispute(db, dispute_id, user)
    if dispute.status == DisputeStatus.resolved:
        raise HTTPException(status_code=400, detail="Dispute is resolved")

    file_url = None
    if file and file.filename:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"File type not allowed")
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File exceeds 10MB limit")
        path = f"disputes/{dispute_id}/{uuid.uuid4()}{ext}"
        file_url = await upload_file(
            settings.SUPABASE_BUCKET_DELIVERABLES, path, content,
            file.content_type or "application/octet-stream"
        )

    msg = DisputeMessage(
        dispute_id=dispute_id,
        author_id=user.id,
        content=data.content,
        file_url=file_url,
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg


async def update_dispute_status(
    db: AsyncSession, dispute_id: uuid.UUID, user: User, new_status: DisputeStatus
) -> Dispute:
    from app.models.user import UserRole
    if user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Admin only")
    result = await db.execute(select(Dispute).where(Dispute.id == dispute_id))
    dispute = result.scalar_one_or_none()
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")
    dispute.status = new_status
    await db.commit()
    await db.refresh(dispute)
    return dispute


async def resolve_dispute(
    db: AsyncSession, dispute_id: uuid.UUID, user: User, data: DisputeResolveRequest
) -> Dispute:
    from app.models.user import UserRole
    from datetime import datetime, timezone
    if user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Admin only")

    result = await db.execute(
        select(Dispute)
        .options(selectinload(Dispute.messages))
        .where(Dispute.id == dispute_id)
    )
    dispute = result.scalar_one_or_none()
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")
    if dispute.status == DisputeStatus.resolved:
        raise HTTPException(status_code=400, detail="Already resolved")

    contract_result = await db.execute(select(Contract).where(Contract.id == dispute.contract_id))
    contract = contract_result.scalar_one_or_none()

    now = datetime.now(timezone.utc)
    dispute.status = DisputeStatus.resolved
    dispute.resolution = data.resolution
    dispute.resolution_comment = data.resolution_comment
    dispute.resolved_by_id = user.id
    dispute.resolved_at = now

    if contract:
        if data.resolution == DisputeResolution.executor:
            await escrow_service.release_funds(db, contract)
        elif data.resolution == DisputeResolution.customer:
            await escrow_service.refund_funds(db, contract)
        elif data.resolution == DisputeResolution.shared:
            await escrow_service.release_shared(db, contract)

        contract.status = ContractStatus.completed

        # Notify both parties
        await notification_service.create_notification(
            db, contract.customer_id, NotificationType.dispute,
            "Dispute resolved",
            f"Dispute resolved: {data.resolution.value}. {data.resolution_comment or ''}",
            related_entity_type="dispute",
            related_entity_id=dispute.id,
        )
        await notification_service.create_notification(
            db, contract.executor_id, NotificationType.dispute,
            "Dispute resolved",
            f"Dispute resolved: {data.resolution.value}. {data.resolution_comment or ''}",
            related_entity_type="dispute",
            related_entity_id=dispute.id,
        )

    await db.commit()
    await db.refresh(dispute)
    return dispute
