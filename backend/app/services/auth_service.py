"""
Authentication service for user authentication and authorization.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User
from app.schemas.auth import TokenResponse
from app.schemas.user import User as UserSchema


async def authenticate_user(db: AsyncSession, username: str, password: str) -> User | None:
    """
    Authenticate a user by username and password.

    Args:
        db: Database session
        username: Username
        password: Plain password

    Returns:
        User if authenticated, None otherwise
    """
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if user is None:
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user


async def create_token_response(user: User) -> TokenResponse:
    """
    Create a token response for a user.

    Args:
        user: Authenticated user

    Returns:
        Token response with access token and user info
    """
    access_token = create_access_token(data={"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserSchema.model_validate(user),
    )


async def create_user(
    db: AsyncSession,
    username: str,
    email: str,
    password: str,
    full_name: str | None = None,
    is_admin: bool = False,
) -> User:
    """
    Create a new user.

    Args:
        db: Database session
        username: Username
        email: Email address
        password: Plain password
        full_name: Full name
        is_admin: Whether user is admin

    Returns:
        Created user
    """
    password_hash = get_password_hash(password)

    user = User(
        username=username,
        email=email,
        password_hash=password_hash,
        full_name=full_name,
        is_admin=is_admin,
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user
