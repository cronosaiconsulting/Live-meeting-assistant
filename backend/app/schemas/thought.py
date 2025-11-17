"""
Pydantic schemas for AI Thought model.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AIThoughtCreate(BaseModel):
    """Schema for creating an AI thought."""

    room_id: UUID
    participant_id: UUID | None = None
    thought_type: str
    content: dict
    confidence: float | None = None
    source_transcript_ids: list[UUID] | None = None
    metadata: dict | None = None


class AIThought(BaseModel):
    """Public AI thought schema."""

    id: UUID
    room_id: UUID
    participant_id: UUID | None
    thought_type: str
    content: dict
    confidence: float | None
    timestamp: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class ThoughtBoardUpdate(BaseModel):
    """WebSocket message for thought board updates."""

    type: str = "thought_board_update"
    data: dict  # Contains topics, action_items, questions, summaries
