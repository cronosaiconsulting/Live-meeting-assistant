"""
Participant model for tracking users in rooms.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, UUID
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.room import Room
    from app.models.transcript import TranscriptSegment


class Participant(Base, UUIDMixin, TimestampMixin):
    """User participation in a room."""

    __tablename__ = "participants"
    __table_args__ = (
        UniqueConstraint("room_id", "livekit_identity", name="uq_room_livekit_identity"),
    )

    room_id: Mapped[UUID] = mapped_column(
        UUID, ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[UUID | None] = mapped_column(
        UUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    livekit_identity: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True
    )
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True
    )
    left_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    role: Mapped[str] = mapped_column(
        String(50), default="participant", nullable=False
    )  # participant, moderator
    metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    room: Mapped["Room"] = relationship("Room", back_populates="participants")
    user: Mapped["User | None"] = relationship("User", back_populates="participants")
    transcript_segments: Mapped[list["TranscriptSegment"]] = relationship(
        "TranscriptSegment",
        back_populates="participant",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Participant(id={self.id}, livekit_identity={self.livekit_identity})>"
