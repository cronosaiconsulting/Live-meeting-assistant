"""
Room model for meeting rooms.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, UUID
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.participant import Participant
    from app.models.transcript import TranscriptSegment
    from app.models.ai_thought import AIThought


class Room(Base, UUIDMixin, TimestampMixin):
    """Meeting room."""

    __tablename__ = "rooms"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    livekit_room_name: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    created_by_user_id: Mapped[UUID | None] = mapped_column(
        UUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(
        String(50), default="active", nullable=False, index=True
    )  # active, ended, archived
    scheduled_start: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    actual_start: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    actual_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    created_by: Mapped["User | None"] = relationship("User", foreign_keys=[created_by_user_id])
    participants: Mapped[list["Participant"]] = relationship(
        "Participant",
        back_populates="room",
        cascade="all, delete-orphan",
    )
    transcript_segments: Mapped[list["TranscriptSegment"]] = relationship(
        "TranscriptSegment",
        back_populates="room",
        cascade="all, delete-orphan",
    )
    ai_thoughts: Mapped[list["AIThought"]] = relationship(
        "AIThought",
        back_populates="room",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Room(id={self.id}, name={self.name}, status={self.status})>"
