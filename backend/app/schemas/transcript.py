"""
Pydantic schemas for Transcript model.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class TranscriptSegmentCreate(BaseModel):
    """Schema for creating a transcript segment."""

    room_id: UUID
    participant_id: UUID
    text: str
    start_timestamp: datetime
    end_timestamp: datetime | None = None
    duration_ms: int | None = None
    is_final: bool = False
    confidence: float | None = None
    language_code: str | None = None
    metadata: dict | None = None


class TranscriptSegment(BaseModel):
    """Public transcript segment schema."""

    id: UUID
    room_id: UUID
    participant_id: UUID
    text: str
    start_timestamp: datetime
    end_timestamp: datetime | None
    duration_ms: int | None
    is_final: bool
    confidence: float | None
    language_code: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TranscriptUpdate(BaseModel):
    """WebSocket message for transcript updates."""

    type: str = "transcript_update"
    data: dict  # Contains participant info and transcript
