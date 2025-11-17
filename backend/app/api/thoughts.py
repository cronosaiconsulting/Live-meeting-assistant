"""
AI Thoughts API routes.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_admin_user
from app.models.ai_thought import AIThought
from app.models.user import User
from app.schemas.thought import AIThought as AIThoughtSchema

router = APIRouter()


@router.get("/{room_id}", response_model=list[AIThoughtSchema])
async def get_room_thoughts(
    room_id: UUID,
    current_user: Annotated[User, Depends(get_current_admin_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    thought_type: str | None = None,
):
    """
    Get AI thoughts for a room (admin only).

    Args:
        room_id: Room ID
        current_user: Current authenticated admin user
        db: Database session
        thought_type: Filter by thought type

    Returns:
        List of AI thoughts
    """
    query = select(AIThought).where(AIThought.room_id == room_id)

    if thought_type:
        query = query.where(AIThought.thought_type == thought_type)

    query = query.order_by(AIThought.timestamp.desc())

    result = await db.execute(query)
    thoughts = list(result.scalars().all())

    return thoughts
