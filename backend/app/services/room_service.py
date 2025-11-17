"""
Room service for managing meeting rooms and participants.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.participant import Participant
from app.models.room import Room
from app.models.user import User
from app.schemas.room import RoomJoinResponse
from app.services.livekit_service import generate_access_token, generate_room_name
from app.config import settings


async def create_room(
    db: AsyncSession,
    name: str,
    created_by: User,
    scheduled_start: datetime | None = None,
) -> Room:
    """
    Create a new meeting room.

    Args:
        db: Database session
        name: Room name
        created_by: User creating the room
        scheduled_start: Scheduled start time

    Returns:
        Created room
    """
    livekit_room_name = generate_room_name()

    room = Room(
        name=name,
        livekit_room_name=livekit_room_name,
        created_by_user_id=created_by.id,
        scheduled_start=scheduled_start,
        status="active",
    )

    db.add(room)
    await db.commit()
    await db.refresh(room)

    return room


async def join_room(
    db: AsyncSession,
    room_id: UUID,
    user: User,
    display_name: str | None = None,
) -> RoomJoinResponse:
    """
    Join a meeting room and generate LiveKit token.

    Args:
        db: Database session
        room_id: Room ID to join
        user: User joining the room
        display_name: Display name for participant

    Returns:
        Join response with room info and LiveKit token

    Raises:
        ValueError: If room not found or inactive
    """
    # Get room
    result = await db.execute(select(Room).where(Room.id == room_id))
    room = result.scalar_one_or_none()

    if room is None:
        raise ValueError("Room not found")

    if room.status != "active":
        raise ValueError("Room is not active")

    # Create or get participant
    participant_identity = f"user_{user.id}"
    result = await db.execute(
        select(Participant).where(
            Participant.room_id == room_id,
            Participant.livekit_identity == participant_identity,
        )
    )
    participant = result.scalar_one_or_none()

    if participant is None:
        # Create new participant
        participant = Participant(
            room_id=room.id,
            user_id=user.id,
            livekit_identity=participant_identity,
            display_name=display_name or user.full_name or user.username,
            role="moderator" if user.is_admin else "participant",
        )
        db.add(participant)
        await db.commit()
        await db.refresh(participant)

    # Update room actual_start if first join
    if room.actual_start is None:
        room.actual_start = datetime.utcnow()
        await db.commit()

    # Generate LiveKit access token
    livekit_token = generate_access_token(
        room_name=room.livekit_room_name,
        participant_identity=participant_identity,
        participant_name=participant.display_name,
    )

    return RoomJoinResponse(
        room=room,
        livekit_token=livekit_token,
        livekit_url=settings.livekit_url,
        participant_id=participant.id,
    )


async def get_room(db: AsyncSession, room_id: UUID) -> Room | None:
    """Get a room by ID."""
    result = await db.execute(select(Room).where(Room.id == room_id))
    return result.scalar_one_or_none()


async def list_rooms(db: AsyncSession, status: str | None = None) -> list[Room]:
    """List all rooms, optionally filtered by status."""
    query = select(Room)
    if status:
        query = query.where(Room.status == status)
    query = query.order_by(Room.created_at.desc())

    result = await db.execute(query)
    return list(result.scalars().all())
