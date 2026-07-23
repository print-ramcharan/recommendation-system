"""add latency profiles table

Revision ID: 719f82e5b0a6
Revises: 93e88d57ae77
Create Date: 2026-07-23 21:35:11.243049

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '719f82e5b0a6'
down_revision: Union[str, Sequence[str], None] = '93e88d57ae77'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'latency_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('route', sa.String(), nullable=False),
        sa.Column('duration_ms', sa.Float(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_latency_profiles_id'), 'latency_profiles', ['id'], unique=False)
    op.create_index(op.f('ix_latency_profiles_route'), 'latency_profiles', ['route'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_latency_profiles_route'), table_name='latency_profiles')
    op.drop_index(op.f('ix_latency_profiles_id'), table_name='latency_profiles')
    op.drop_table('latency_profiles')
