import uuid
import json
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.contract import (
    Contract, ContractClause, Milestone, Deliverable,
    ContractStatus, MilestoneStatus, ClauseType
)
from app.models.review import Review
from app.models.user import User
from app.models.notification import NotificationType
from app.schemas.contract import (
    ContractUpdate, ClauseUpdate, MilestoneCreate, MilestoneUpdate, ReviewCreate
)
from app.services import escrow_service, notification_service
from app.core.security import generate_contract_hash
from app.core.config import settings
from app.core.storage import upload_file, get_signed_url

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".zip", ".png", ".jpg", ".jpeg"}
MAX_FILE_SIZE = 10 * 1024 * 1024


async def get_contract(db: AsyncSession, contract_id: uuid.UUID, user: User) -> Contract:
    result = await db.execute(
        select(Contract)
        .options(
            selectinload(Contract.clauses),
            selectinload(Contract.milestones),
            selectinload(Contract.deliverables),
            selectinload(Contract.escrow_transactions),
        )
        .where(Contract.id == contract_id)
    )
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    if contract.customer_id != user.id and contract.executor_id != user.id:
        if user.role.value != "admin":
            raise HTTPException(status_code=403, detail="Not authorized")
    return contract


async def update_contract(
    db: AsyncSession, contract_id: uuid.UUID, user: User, data: ContractUpdate
) -> Contract:
    contract = await get_contract(db, contract_id, user)
    if contract.status != ContractStatus.draft:
        raise HTTPException(status_code=400, detail="Can only update draft contracts")
    if contract.customer_id != user.id:
        raise HTTPException(status_code=403, detail="Only customer can update contract")

    for field, val in data.model_dump(exclude_unset=True).items():
        setattr(contract, field, val)

    if data.total_amount is not None:
        contract.platform_fee = round(float(data.total_amount) * settings.PLATFORM_FEE_PERCENT / 100, 2)

    await db.commit()
    await db.refresh(contract)
    return await get_contract(db, contract_id, user)


async def update_clauses(
    db: AsyncSession, contract_id: uuid.UUID, user: User, updates: List[ClauseUpdate]
) -> Contract:
    contract = await get_contract(db, contract_id, user)
    if contract.status not in (ContractStatus.draft, ContractStatus.signed):
        raise HTTPException(status_code=400, detail="Cannot update clauses in current status")

    clauses_map = {c.id: c for c in contract.clauses}
    for upd in updates:
        clause = clauses_map.get(upd.id)
        if not clause:
            continue
        if upd.content is not None:
            clause.content = upd.content
        if upd.position is not None:
            clause.position = upd.position

    await db.commit()
    return await get_contract(db, contract_id, user)


async def sign_contract(
    db: AsyncSession, contract_id: uuid.UUID, user: User
) -> Contract:
    contract = await get_contract(db, contract_id, user)

    if contract.status not in (ContractStatus.draft,):
        raise HTTPException(status_code=400, detail="Contract is not in draft status")

    now = datetime.now(timezone.utc)
    is_customer = contract.customer_id == user.id
    is_executor = contract.executor_id == user.id

    if not is_customer and not is_executor:
        raise HTTPException(status_code=403, detail="Not a party to this contract")

    if is_customer and contract.customer_signed_at:
        raise HTTPException(status_code=400, detail="Already signed")
    if is_executor and contract.executor_signed_at:
        raise HTTPException(status_code=400, detail="Already signed")

    if is_customer:
        contract.customer_signed_at = now
    else:
        contract.executor_signed_at = now

    # Both signed?
    if contract.customer_signed_at and contract.executor_signed_at:
        contract.signed_at = now
        # Generate contract hash
        clauses_sorted = sorted(contract.clauses, key=lambda c: c.position)
        clauses_data = [
            {"type": c.clause_type.value, "content": c.content, "position": c.position}
            for c in clauses_sorted
        ]
        clauses_json = json.dumps(clauses_data, sort_keys=True)
        contract.contract_hash = generate_contract_hash(
            clauses_json,
            str(contract.total_amount),
            str(contract.customer_id),
            str(contract.executor_id),
            now.isoformat(),
        )
        contract.status = ContractStatus.in_progress

        await db.flush()
        await escrow_service.lock_funds(db, contract)

        await notification_service.create_notification(
            db, contract.customer_id, NotificationType.payment,
            "Contract signed & funds locked",
            "Both parties signed. Escrow funds are locked.",
            related_entity_type="contract",
            related_entity_id=contract.id,
        )
        await notification_service.create_notification(
            db, contract.executor_id, NotificationType.payment,
            "Contract signed & funds locked",
            "Both parties signed. Escrow funds are locked. Work can begin.",
            related_entity_type="contract",
            related_entity_id=contract.id,
        )

    await db.commit()
    return await get_contract(db, contract_id, user)


async def add_milestone(
    db: AsyncSession, contract_id: uuid.UUID, user: User, data: MilestoneCreate
) -> Milestone:
    contract = await get_contract(db, contract_id, user)
    if contract.status not in (ContractStatus.draft, ContractStatus.in_progress):
        raise HTTPException(status_code=400, detail="Cannot add milestone in current status")
    if contract.customer_id != user.id and contract.executor_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    ms = Milestone(
        contract_id=contract_id,
        title=data.title,
        description=data.description,
        amount=data.amount,
        deadline=data.deadline,
        position=data.position,
    )
    db.add(ms)
    await db.commit()
    await db.refresh(ms)
    return ms


async def update_milestone(
    db: AsyncSession, contract_id: uuid.UUID, milestone_id: uuid.UUID,
    user: User, data: MilestoneUpdate
) -> Milestone:
    result = await db.execute(
        select(Milestone).where(
            Milestone.id == milestone_id, Milestone.contract_id == contract_id
        )
    )
    ms = result.scalar_one_or_none()
    if not ms:
        raise HTTPException(status_code=404, detail="Milestone not found")

    for field, val in data.model_dump(exclude_unset=True).items():
        setattr(ms, field, val)
    await db.commit()
    await db.refresh(ms)
    return ms


async def upload_deliverable(
    db: AsyncSession,
    contract_id: uuid.UUID,
    user: User,
    file: UploadFile,
    description: str,
    milestone_id: Optional[uuid.UUID] = None,
) -> Deliverable:
    import os
    contract = await get_contract(db, contract_id, user)
    if contract.status != ContractStatus.in_progress:
        raise HTTPException(status_code=400, detail="Contract is not in progress")
    if contract.executor_id != user.id:
        raise HTTPException(status_code=403, detail="Only executor can upload deliverables")

    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type {ext} not allowed")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File exceeds 10MB limit")

    path = f"{contract_id}/{uuid.uuid4()}{ext}"
    file_url = await upload_file(
        settings.SUPABASE_BUCKET_DELIVERABLES, path, content,
        file.content_type or "application/octet-stream"
    )

    deliverable = Deliverable(
        contract_id=contract_id,
        milestone_id=milestone_id,
        file_url=file_url,
        file_name=file.filename or "file",
        file_size=len(content),
        description=description,
        submitted_by_id=user.id,
    )
    db.add(deliverable)

    await notification_service.create_notification(
        db, contract.customer_id, NotificationType.contract,
        "New deliverable submitted",
        f"Executor submitted a new deliverable.",
        related_entity_type="deliverable",
        related_entity_id=deliverable.id,
    )
    await db.commit()
    await db.refresh(deliverable)
    return deliverable


async def get_deliverable_download_url(
    db: AsyncSession, contract_id: uuid.UUID, deliverable_id: uuid.UUID, user: User
) -> str:
    contract = await get_contract(db, contract_id, user)
    result = await db.execute(
        select(Deliverable).where(
            Deliverable.id == deliverable_id,
            Deliverable.contract_id == contract_id,
        )
    )
    d = result.scalar_one_or_none()
    if not d:
        raise HTTPException(status_code=404, detail="Deliverable not found")

    import os
    path = d.file_url.split("/")[-1]
    # Reconstruct the storage path
    storage_path = f"{contract_id}/{path}"
    signed_url = await get_signed_url(settings.SUPABASE_BUCKET_DELIVERABLES, storage_path)
    return signed_url


async def accept_contract(db: AsyncSession, contract_id: uuid.UUID, user: User) -> Contract:
    contract = await get_contract(db, contract_id, user)
    if contract.customer_id != user.id:
        raise HTTPException(status_code=403, detail="Only customer can accept")
    if contract.status != ContractStatus.in_progress:
        raise HTTPException(status_code=400, detail="Contract is not in progress")

    await escrow_service.release_funds(db, contract)
    contract.status = ContractStatus.completed

    await notification_service.create_notification(
        db, contract.executor_id, NotificationType.payment,
        "Contract completed",
        "Customer accepted the work. Funds have been released.",
        related_entity_type="contract",
        related_entity_id=contract.id,
    )
    await db.commit()
    return await get_contract(db, contract_id, user)


async def reject_contract(db: AsyncSession, contract_id: uuid.UUID, user: User) -> Contract:
    contract = await get_contract(db, contract_id, user)
    if contract.customer_id != user.id:
        raise HTTPException(status_code=403, detail="Only customer can reject")
    if contract.status != ContractStatus.in_progress:
        raise HTTPException(status_code=400, detail="Contract is not in progress")

    contract.status = ContractStatus.disputed

    # Open a dispute automatically
    from app.models.dispute import Dispute, DisputeStatus
    dispute = Dispute(
        contract_id=contract_id,
        initiated_by_id=user.id,
        description="Customer rejected the work.",
        status=DisputeStatus.open,
    )
    db.add(dispute)
    await db.flush()

    await notification_service.create_notification(
        db, contract.executor_id, NotificationType.dispute,
        "Work rejected - Dispute opened",
        "Customer rejected the work. A dispute has been opened.",
        related_entity_type="dispute",
        related_entity_id=dispute.id,
    )
    await db.commit()
    return await get_contract(db, contract_id, user)


async def create_review(
    db: AsyncSession, contract_id: uuid.UUID, user: User, data: ReviewCreate
) -> Review:
    contract = await get_contract(db, contract_id, user)
    if contract.status != ContractStatus.completed:
        raise HTTPException(status_code=400, detail="Can only review completed contracts")

    # Determine recipient
    if contract.customer_id == user.id:
        recipient_id = contract.executor_id
    elif contract.executor_id == user.id:
        recipient_id = contract.customer_id
    else:
        raise HTTPException(status_code=403, detail="Not a party to this contract")

    existing = await db.execute(
        select(Review).where(
            Review.contract_id == contract_id,
            Review.author_id == user.id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Already reviewed this contract")

    review = Review(
        contract_id=contract_id,
        author_id=user.id,
        recipient_id=recipient_id,
        rating=data.rating,
        comment=data.comment,
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)
    return review
