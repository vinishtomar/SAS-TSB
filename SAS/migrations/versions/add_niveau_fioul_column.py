"""Add niveau_fioul column to equipment

Revision ID: add_niveau_fioul_column
Revises: add_fields_to_equipment
Create Date: 2025-08-04 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_niveau_fioul_column'
down_revision = 'add_fields_to_equipment' # Fait référence à notre migration manuelle précédente
branch_labels = None
depends_on = None


def upgrade():
    # Instruction pour ajouter la colonne 'niveau_fioul' à la table 'equipment'
    op.add_column('equipment', sa.Column('niveau_fioul', sa.String(length=50), nullable=True))


def downgrade():
    # Instruction pour annuler le changement (supprimer la colonne)
    op.drop_column('equipment', 'niveau_fioul')
