"""
Transcripts API routes.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.transcript import TranscriptSegment
from app.models.user import User
from app.schemas.transcript import TranscriptSegment as TranscriptSegmentSchema

router = APIRouter()


@router.get("/{room_id}", response_model=list[TranscriptSegmentSchema])
async def get_room_transcripts(
    room_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    is_final: bool | None = None,
):
    """
    Get transcripts for a room.

    Args:
        room_id: Room ID
        current_user: Current authenticated user
        db: Database session
        is_final: Filter by is_final flag

    Returns:
        List of transcript segments
    """
    query = select(TranscriptSegment).where(TranscriptSegment.room_id == room_id)

    if is_final is not None:
        query = query.where(TranscriptSegment.is_final == is_final)

    query = query.order_by(TranscriptSegment.start_timestamp)

    result = await db.execute(query)
    transcripts = list(result.scalars().all())

    return transcripts
