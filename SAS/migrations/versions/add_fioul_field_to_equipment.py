"""Add fioul level to equipment

Revision ID: add_fioul_field_to_equipment
Revises: aae6d95ca4cb
Create Date: 2025-08-01 10:35:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_fioul_field_to_equipment'
# Remplacez 'aae6d95ca4cb' par l'ID de votre DERNIÈRE migration réussie si ce n'est pas la bonne
down_revision = 'aae6d95ca4cb' 
branch_labels = None
depends_on = None


def upgrade():
    # ### Instruction manuelle pour ajouter la colonne 'niveau_fioul' ###
    op.add_column('equipment', sa.Column('niveau_fioul', sa.String(length=50), nullable=True))
    # ### Fin des instructions ###


def downgrade():
    # ### Instruction pour annuler le changement ###
    op.drop_column('equipment', 'niveau_fioul')
    # ### Fin des instructions ###

