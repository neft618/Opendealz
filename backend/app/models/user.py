import uuid
import enum
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import String, Boolean, DateTime, Enum as SAEnum, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class UserRole(str, enum.Enum):
    customer = "customer"
    executor = "executor"
    admin = "admin"


class Specialization(str, enum.Enum):
    web_development = "web_development"
    mobile_development = "mobile_development"
    data_science = "data_science"
    design = "design"
    marketing = "marketing"
    other = "other"


class User(Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="user_role", create_type=True),
        default=UserRole.customer,
        nullable=False,
    )
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    wallet_address: Mapped[Optional[str]] = mapped_column(String(42), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    profile: Mapped[Optional["Profile"]] = relationship(
        "Profile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    orders: Mapped[List["Order"]] = relationship(
        "Order", foreign_keys="Order.customer_id", back_populates="customer"
    )
    executor_orders: Mapped[List["Order"]] = relationship(
        "Order", foreign_keys="Order.executor_id", back_populates="executor"
    )
    applications: Mapped[List["Application"]] = relationship(
        "Application", foreign_keys="Application.executor_id", back_populates="executor"
    )
    customer_contracts: Mapped[List["Contract"]] = relationship(
        "Contract", foreign_keys="Contract.customer_id", back_populates="customer"
    )
    executor_contracts: Mapped[List["Contract"]] = relationship(
        "Contract", foreign_keys="Contract.executor_id", back_populates="executor"
    )
    reviews_given: Mapped[List["Review"]] = relationship(
        "Review", foreign_keys="Review.author_id", back_populates="author"
    )
    reviews_received: Mapped[List["Review"]] = relationship(
        "Review", foreign_keys="Review.recipient_id", back_populates="recipient"
    )
    notifications: Mapped[List["Notification"]] = relationship(
        "Notification", back_populates="user"
    )
    disputes_initiated: Mapped[List["Dispute"]] = relationship(
        "Dispute", foreign_keys="Dispute.initiated_by_id", back_populates="initiated_by"
    )
    disputes_resolved: Mapped[List["Dispute"]] = relationship(
        "Dispute", foreign_keys="Dispute.resolved_by_id", back_populates="resolved_by"
    )
    dispute_messages: Mapped[List["DisputeMessage"]] = relationship(
        "DisputeMessage", back_populates="author"
    )
    deliverables_submitted: Mapped[List["Deliverable"]] = relationship(
        "Deliverable", back_populates="submitted_by"
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog", back_populates="user"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email}>"


class Profile(Base):
    __tablename__ = "profiles"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_profiles_user_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    skills: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    specialization: Mapped[Optional[Specialization]] = mapped_column(
        SAEnum(Specialization, name="specialization", create_type=True), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user: Mapped["User"] = relationship("User", back_populates="profile")
    portfolios: Mapped[List["Portfolio"]] = relationship(
        "Portfolio", back_populates="profile", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Profile id={self.id} user_id={self.user_id}>"


class Portfolio(Base):
    __tablename__ = "portfolios"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    file_url: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    profile: Mapped["Profile"] = relationship("Profile", back_populates="portfolios")

    def __repr__(self) -> str:
        return f"<Portfolio id={self.id} title={self.title}>"
