"""Add detailed fields to Equipment

Revision ID: add_fields_to_equipment
Revises: aae6d95ca4cb
Create Date: 2025-08-01 16:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_fields_to_equipment'
down_revision = 'aae6d95ca4cb' # Ceci doit correspondre à la révision précédente
branch_labels = None
depends_on = None


def upgrade():
    # ### Instructions manuelles pour mettre à jour la table 'equipment' ###
    op.add_column('equipment', sa.Column('notes', sa.Text(), nullable=True))
    op.add_column('equipment', sa.Column('immatriculation', sa.String(length=50), nullable=True))
    op.add_column('equipment', sa.Column('responsable_id', sa.Integer(), nullable=True))
    op.add_column('equipment', sa.Column('date_debut_responsabilite', sa.Date(), nullable=True))
    op.add_column('equipment', sa.Column('date_fin_responsabilite', sa.Date(), nullable=True))
    op.add_column('equipment', sa.Column('type_engin', sa.String(length=100), nullable=True))
    op.add_column('equipment', sa.Column('hauteur', sa.Float(), nullable=True))
    op.add_column('equipment', sa.Column('date_vgp', sa.Date(), nullable=True))
    op.add_column('equipment', sa.Column('nombre_cles', sa.Integer(), nullable=True))
    op.add_column('equipment', sa.Column('photo_fuel_url', sa.String(length=500), nullable=True))
    op.add_column('equipment', sa.Column('type_materiel', sa.String(length=100), nullable=True))
    op.add_column('equipment', sa.Column('etat', sa.String(length=50), nullable=True))
    op.create_foreign_key('fk_equipment_responsable_id_employee', 'equipment', 'employee', ['responsable_id'], ['id'])
    # ### Fin des instructions ###


def downgrade():
    # ### Instructions pour annuler les changements ###
    op.drop_constraint('fk_equipment_responsable_id_employee', 'equipment', type_='foreignkey')
    op.drop_column('equipment', 'etat')
    op.drop_column('equipment', 'type_materiel')
    op.drop_column('equipment', 'photo_fuel_url')
    op.drop_column('equipment', 'nombre_cles')
    op.drop_column('equipment', 'date_vgp')
    op.drop_column('equipment', 'hauteur')
    op.drop_column('equipment', 'type_engin')
    op.drop_column('equipment', 'date_fin_responsabilite')
    op.drop_column('equipment', 'date_debut_responsabilite')
    op.drop_column('equipment', 'responsable_id')
    op.drop_column('equipment', 'immatriculation')
    op.drop_column('equipment', 'notes')
    # ### Fin des instructions ###
