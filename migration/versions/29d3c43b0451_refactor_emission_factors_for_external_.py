"""refactor emission_factors for external providers

Revision ID: 29d3c43b0451
Revises: c2edaf8a69b0
Create Date: 2026-02-11 09:17:05.781202

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '29d3c43b0451'
down_revision: Union[str, Sequence[str], None] = 'c2edaf8a69b0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.drop_table("emission_factors")

    op.create_table(
        "emission_factors",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("external_id", sa.String(), nullable=True),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("geography", sa.String(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("co2e_per_currency", sa.Numeric(), nullable=False),
        sa.Column("source_url", sa.String(), nullable=True),
        sa.Column("methodology", sa.String(), nullable=True),
        sa.Column("version", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

def downgrade():
    op.drop_table("emission_factors")

    # ### end Alembic commands ###
