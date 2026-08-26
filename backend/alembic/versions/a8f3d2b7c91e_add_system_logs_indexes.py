"""Add indexes to system_logs table

Revision ID: a8f3d2b7c91e
Revises: f7b1a97f1778
Create Date: 2026-08-26 08:15:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'a8f3d2b7c91e'
down_revision: Union[str, Sequence[str], None] = 'f7b1a97f1778'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add indexes to support Grafana time-range and filter queries."""
    op.create_index('ix_system_logs_created_at', 'system_logs', ['created_at'])
    op.create_index('ix_system_logs_status_code', 'system_logs', ['status_code'])
    op.create_index('ix_system_logs_level', 'system_logs', ['level'])


def downgrade() -> None:
    """Remove indexes."""
    op.drop_index('ix_system_logs_level', table_name='system_logs')
    op.drop_index('ix_system_logs_status_code', table_name='system_logs')
    op.drop_index('ix_system_logs_created_at', table_name='system_logs')
