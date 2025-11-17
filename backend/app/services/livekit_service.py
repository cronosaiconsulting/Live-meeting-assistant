"""
LiveKit integration service for generating access tokens and managing rooms.
"""

import uuid
from datetime import timedelta

from livekit import api

from app.config import settings


def generate_room_name() -> str:
    """Generate a unique room name for LiveKit."""
    return f"room_{uuid.uuid4().hex[:12]}"


def generate_access_token(
    room_name: str,
    participant_identity: str,
    participant_name: str | None = None,
) -> str:
    """
    Generate a LiveKit access token for a participant.

    Args:
        room_name: Name of the LiveKit room
        participant_identity: Unique participant identifier
        participant_name: Display name for participant

    Returns:
        LiveKit access token
    """
    # Create access token with grants
    token = api.AccessToken(
        api_key=settings.livekit_api_key,
        api_secret=settings.livekit_api_secret,
    )

    # Set video grants
    token.with_grants(
        api.VideoGrants(
            room_join=True,
            room=room_name,
            can_publish=True,
            can_subscribe=True,
            can_publish_data=True,
        )
    )

    # Set identity and name
    token.with_identity(participant_identity)
    if participant_name:
        token.with_name(participant_name)

    # Set token validity (24 hours)
    token.with_ttl(timedelta(hours=24))

    return token.to_jwt()
