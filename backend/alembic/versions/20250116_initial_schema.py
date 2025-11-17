"""Initial schema with all tables

Revision ID: 001_initial
Revises:
Create Date: 2025-01-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('username', sa.String(255), nullable=False, unique=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_users_username', 'users', ['username'])
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_is_admin', 'users', ['is_admin'])

    # Create rooms table
    op.create_table(
        'rooms',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('livekit_room_name', sa.String(255), nullable=False, unique=True),
        sa.Column('created_by_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('scheduled_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('actual_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('actual_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_rooms_livekit_room_name', 'rooms', ['livekit_room_name'])
    op.create_index('ix_rooms_created_by_user_id', 'rooms', ['created_by_user_id'])
    op.create_index('ix_rooms_status', 'rooms', ['status'])
    op.create_index('ix_rooms_scheduled_start', 'rooms', ['scheduled_start'])

    # Create participants table
    op.create_table(
        'participants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('room_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('livekit_identity', sa.String(255), nullable=False),
        sa.Column('display_name', sa.String(255), nullable=True),
        sa.Column('joined_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('left_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('role', sa.String(50), nullable=False, server_default='participant'),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['room_id'], ['rooms.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('room_id', 'livekit_identity', name='uq_room_livekit_identity'),
    )
    op.create_index('ix_participants_room_id', 'participants', ['room_id'])
    op.create_index('ix_participants_user_id', 'participants', ['user_id'])
    op.create_index('ix_participants_livekit_identity', 'participants', ['livekit_identity'])
    op.create_index('ix_participants_joined_at', 'participants', ['joined_at'])

    # Create transcript_segments table
    op.create_table(
        'transcript_segments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('room_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('participant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('start_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_timestamp', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('is_final', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('language_code', sa.String(10), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['room_id'], ['rooms.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['participant_id'], ['participants.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_transcript_segments_room_id', 'transcript_segments', ['room_id'])
    op.create_index('ix_transcript_segments_participant_id', 'transcript_segments', ['participant_id'])
    op.create_index('ix_transcript_segments_start_timestamp', 'transcript_segments', ['start_timestamp'])
    op.create_index('ix_transcript_segments_is_final', 'transcript_segments', ['is_final'])

    # Create ai_thoughts table
    op.create_table(
        'ai_thoughts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('room_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('participant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('thought_type', sa.String(50), nullable=False),
        sa.Column('content', postgresql.JSONB(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('source_transcript_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['room_id'], ['rooms.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['participant_id'], ['participants.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_ai_thoughts_room_id', 'ai_thoughts', ['room_id'])
    op.create_index('ix_ai_thoughts_participant_id', 'ai_thoughts', ['participant_id'])
    op.create_index('ix_ai_thoughts_thought_type', 'ai_thoughts', ['thought_type'])
    op.create_index('ix_ai_thoughts_timestamp', 'ai_thoughts', ['timestamp'])
    op.create_index('ix_ai_thoughts_source_transcript_ids', 'ai_thoughts', ['source_transcript_ids'], postgresql_using='gin')


def downgrade() -> None:
    op.drop_table('ai_thoughts')
    op.drop_table('transcript_segments')
    op.drop_table('participants')
    op.drop_table('rooms')
    op.drop_table('users')
