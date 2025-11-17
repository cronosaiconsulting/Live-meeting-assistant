"""
AI thought model for storing LLM-generated insights.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, String, UUID, ARRAY
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.room import Room
    from app.models.participant import Participant


class AIThought(Base, UUIDMixin, TimestampMixin):
    """AI-generated insight or thought about the meeting."""

    __tablename__ = "ai_thoughts"

    room_id: Mapped[UUID] = mapped_column(
        UUID, ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False, index=True
    )
    participant_id: Mapped[UUID | None] = mapped_column(
        UUID, ForeignKey("participants.id", ondelete="SET NULL"), nullable=True, index=True
    )
    thought_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # topic, action_item, question, summary, sentiment
    content: Mapped[dict] = mapped_column(JSONB, nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_transcript_ids: Mapped[list[UUID] | None] = mapped_column(
        ARRAY(UUID), nullable=True
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True
    )
    metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    room: Mapped["Room"] = relationship("Room", back_populates="ai_thoughts")
    participant: Mapped["Participant | None"] = relationship("Participant")

    def __repr__(self) -> str:
        return f"<AIThought(id={self.id}, type={self.thought_type})>"
