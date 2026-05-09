import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.core.config import settings
from app.models.user import User, Profile, UserRole
from app.models.audit import AuditLog
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from app.services.notification_service import create_notification, send_email
from app.models.notification import NotificationType
import hashlib

logger = logging.getLogger(__name__)


def _audit_hash(entity_id: str, action: str, ts: str) -> str:
    return hashlib.sha256(f"{entity_id}:{action}:{ts}".encode()).hexdigest()


async def register_user(
    db: AsyncSession,
    data: RegisterRequest,
    ip_address: Optional[str] = None,
) -> User:
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
    )
    db.add(user)
    await db.flush()

    profile = Profile(user_id=user.id)
    db.add(profile)
    await db.flush()

    ts = datetime.now(timezone.utc).isoformat()
    tx_hash = _audit_hash(str(user.id), "user_register", ts)
    audit = AuditLog(
        entity_type="user",
        entity_id=user.id,
        action="user_register",
        user_id=user.id,
        payload={"email": user.email},
        tx_hash=tx_hash,
        ip_address=ip_address,
    )
    db.add(audit)

    await create_notification(
        db, user.id, NotificationType.system,
        "Welcome to OpenDealz!",
        f"Hi {user.full_name}, welcome to OpenDealz.",
    )

    await db.commit()
    await db.refresh(user)

    await send_email(
        user.email,
        "Welcome to OpenDealz",
        f"Hi {user.full_name},\n\nWelcome to OpenDealz! Your account has been created.",
    )

    return user


async def login_user(
    db: AsyncSession,
    data: LoginRequest,
) -> TokenResponse:
    result = await db.execute(
        select(User).where(User.email == data.email)
    )
    user = result.scalar_one_or_none()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account deactivated")

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


async def refresh_tokens(db: AsyncSession, refresh_token: str) -> TokenResponse:
    payload = decode_token(refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    access_token = create_access_token({"sub": str(user.id)})
    new_refresh = create_refresh_token({"sub": str(user.id)})
    return TokenResponse(access_token=access_token, refresh_token=new_refresh)


async def ensure_demo_users(db: AsyncSession) -> None:
    if not settings.DEMO_USERS_ENABLED:
        return
    if not all([
        settings.DEMO_CUSTOMER_EMAIL,
        settings.DEMO_CUSTOMER_PASSWORD,
        settings.DEMO_EXECUTOR_EMAIL,
        settings.DEMO_EXECUTOR_PASSWORD,
    ]):
        logger.warning("Demo users are enabled but credentials are not fully configured")
        return

    demo_users = [
        {
            "email": settings.DEMO_CUSTOMER_EMAIL,
            "password": settings.DEMO_CUSTOMER_PASSWORD,
            "full_name": "Demo Customer",
            "role": UserRole.customer,
        },
        {
            "email": settings.DEMO_EXECUTOR_EMAIL,
            "password": settings.DEMO_EXECUTOR_PASSWORD,
            "full_name": "Demo Executor",
            "role": UserRole.executor,
        },
    ]

    created_count = 0
    for entry in demo_users:
        result = await db.execute(select(User).where(User.email == entry["email"]))
        user = result.scalar_one_or_none()
        if user:
            continue

        user = User(
            email=entry["email"],
            password_hash=hash_password(entry["password"]),
            full_name=entry["full_name"],
            role=entry["role"],
        )
        db.add(user)
        await db.flush()
        db.add(Profile(user_id=user.id))
        created_count += 1

    if created_count:
        await db.commit()
        logger.info("Created %d demo users", created_count)
