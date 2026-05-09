import uuid
from typing import Optional

from sqlalchemy import SmallInteger, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (
        UniqueConstraint("contract_id", "author_id", name="uq_review_contract_author"),
    )

    contract_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("contracts.id", ondelete="RESTRICT"), nullable=False
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    recipient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    rating: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    contract: Mapped["Contract"] = relationship("Contract", back_populates="reviews")
    author: Mapped["User"] = relationship(
        "User", foreign_keys=[author_id], back_populates="reviews_given"
    )
    recipient: Mapped["User"] = relationship(
        "User", foreign_keys=[recipient_id], back_populates="reviews_received"
    )

    def __repr__(self) -> str:
        return f"<Review id={self.id} rating={self.rating}>"
