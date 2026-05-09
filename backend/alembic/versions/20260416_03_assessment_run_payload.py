"""add assessment run payload

Revision ID: 20260416_03
Revises: 20260416_02
Create Date: 2026-04-16
"""

from alembic import op
import sqlalchemy as sa


revision = "20260416_03"
down_revision = "20260416_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("assessment_runs", sa.Column("job_payload_json", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("assessment_runs", "job_payload_json")
