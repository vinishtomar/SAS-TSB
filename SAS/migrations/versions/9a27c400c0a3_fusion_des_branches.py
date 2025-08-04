"""Fusion des branches

Revision ID: 9a27c400c0a3
Revises: add_fioul_field_to_equipment, add_niveau_fioul_column
Create Date: 2025-08-04 11:17:45.971820

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9a27c400c0a3'
down_revision = ('add_fioul_field_to_equipment', 'add_niveau_fioul_column')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
