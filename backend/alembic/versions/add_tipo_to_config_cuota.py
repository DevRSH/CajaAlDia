"""add tipo and nombre_especial to config_cuota, create cuota_especial_alumnos table

Revision ID: add_tipo_to_config_cuota
Revises: update_notificaciones_email_tipo_nullable
Create Date: 2026-05-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = 'add_tipo_to_config_cuota'
down_revision: Union[str, None] = 'update_notificaciones_email_tipo_nullable'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Agregar columnas tipo y nombre_especial a config_cuotas
    with op.batch_alter_table('config_cuotas', schema=None) as batch_op:
        batch_op.add_column(sa.Column('tipo', sa.String(length=20), nullable=False, server_default='curso'))
        batch_op.add_column(sa.Column('nombre_especial', sa.String(length=200), nullable=True))

    # Crear tabla cuota_especial_alumnos
    op.create_table(
        'cuota_especial_alumnos',
        sa.Column('id', sa.CHAR(length=36), nullable=False),
        sa.Column('config_cuota_id', sa.CHAR(length=36), nullable=False),
        sa.Column('alumno_id', sa.CHAR(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['alumno_id'], ['alumnos.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['config_cuota_id'], ['config_cuotas.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('config_cuota_id', 'alumno_id', name='uq_cuota_especial_alumno')
    )


def downgrade() -> None:
    # Eliminar tabla cuota_especial_alumnos
    op.drop_table('cuota_especial_alumnos')

    # Eliminar columnas de config_cuotas
    with op.batch_alter_table('config_cuotas', schema=None) as batch_op:
        batch_op.drop_column('nombre_especial')
        batch_op.drop_column('tipo')
