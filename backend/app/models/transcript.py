"""
Transcript segment model for storing speech-to-text results.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UUID
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDMixin

if TYPE_CHECKING:
    from app.models.room import Room
    from app.models.participant import Participant


class TranscriptSegment(Base, UUIDMixin):
    """Speech-to-text transcript segment."""

    __tablename__ = "transcript_segments"

    room_id: Mapped[UUID] = mapped_column(
        UUID, ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False, index=True
    )
    participant_id: Mapped[UUID] = mapped_column(
        UUID, ForeignKey("participants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    start_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    end_timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_final: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, index=True
    )
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    language_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    # Relationships
    room: Mapped["Room"] = relationship("Room", back_populates="transcript_segments")
    participant: Mapped["Participant"] = relationship(
        "Participant", back_populates="transcript_segments"
    )

    def __repr__(self) -> str:
        return f"<TranscriptSegment(id={self.id}, text={self.text[:50]}...)>"
