"""
Rooms API routes.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.room import Room, RoomCreate, RoomJoinRequest, RoomJoinResponse
from app.services.room_service import create_room, join_room, get_room, list_rooms

router = APIRouter()


@router.post("/create", response_model=Room, status_code=status.HTTP_201_CREATED)
async def create_new_room(
    request: RoomCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Create a new meeting room.

    Args:
        request: Room creation request
        current_user: Current authenticated user
        db: Database session

    Returns:
        Created room
    """
    room = await create_room(
        db=db,
        name=request.name,
        created_by=current_user,
        scheduled_start=request.scheduled_start,
    )

    return room


@router.post("/join", response_model=RoomJoinResponse)
async def join_existing_room(
    request: RoomJoinRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Join an existing meeting room and get LiveKit token.

    Args:
        request: Room join request
        current_user: Current authenticated user
        db: Database session

    Returns:
        Join response with LiveKit token

    Raises:
        HTTPException: If room not found or inactive
    """
    try:
        join_response = await join_room(
            db=db,
            room_id=request.room_id,
            user=current_user,
            display_name=request.display_name,
        )
        return join_response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/{room_id}", response_model=Room)
async def get_room_by_id(
    room_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Get room details by ID.

    Args:
        room_id: Room ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Room details

    Raises:
        HTTPException: If room not found
    """
    room = await get_room(db, room_id)

    if room is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found",
        )

    return room


@router.get("/", response_model=list[Room])
async def list_all_rooms(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    status: str | None = None,
):
    """
    List all rooms.

    Args:
        current_user: Current authenticated user
        db: Database session
        status: Optional status filter (active, ended, archived)

    Returns:
        List of rooms
    """
    rooms = await list_rooms(db, status=status)
    return rooms
