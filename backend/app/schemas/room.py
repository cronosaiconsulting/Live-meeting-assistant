"""
Pydantic schemas for Room model.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class RoomBase(BaseModel):
    """Base room schema."""

    name: str = Field(..., min_length=1, max_length=255)


class RoomCreate(RoomBase):
    """Schema for creating a room."""

    scheduled_start: datetime | None = None


class RoomUpdate(BaseModel):
    """Schema for updating a room."""

    name: str | None = Field(None, min_length=1, max_length=255)
    status: str | None = None  # active, ended, archived


class Room(RoomBase):
    """Public room schema."""

    id: UUID
    livekit_room_name: str
    created_by_user_id: UUID | None
    status: str
    scheduled_start: datetime | None
    actual_start: datetime | None
    actual_end: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RoomJoinRequest(BaseModel):
    """Request to join a room."""

    room_id: UUID
    display_name: str | None = None


class RoomJoinResponse(BaseModel):
    """Response when joining a room."""

    room: Room
    livekit_token: str
    livekit_url: str
    participant_id: UUID
