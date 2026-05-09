"""Sprint 7: agregar tabla usuarios y mejorar notificaciones_email

Revision ID: sprint7_usuarios
Revises: update_notificaciones_tipo
Create Date: 2026-05-09 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "sprint7_usuarios"
down_revision: Union[str, None] = "5a045573aaaf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Tabla usuarios
    op.create_table(
        "usuarios",
        sa.Column("id", sa.CHAR(length=36), nullable=False),
        sa.Column("nombre", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("rol", sa.String(length=50), nullable=False, server_default="tesorera"),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="uq_usuarios_email"),
    )

    # Agregar columnas nuevas a notificaciones_email (ADD COLUMN compatible con PostgreSQL y SQLite)
    op.add_column("notificaciones_email", sa.Column("alumno_nombre", sa.String(length=255), nullable=True))
    op.add_column("notificaciones_email", sa.Column("error_detalle", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("notificaciones_email", "error_detalle")
    op.drop_column("notificaciones_email", "alumno_nombre")
    op.drop_table("usuarios")
