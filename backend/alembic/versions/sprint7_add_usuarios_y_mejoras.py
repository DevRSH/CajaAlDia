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

    # Agregar columnas nuevas a notificaciones_email usando recreación de tabla (SQLite)
    op.create_table(
        "notificaciones_email_v2",
        sa.Column("id", sa.CHAR(length=36), nullable=False),
        sa.Column("pago_cuota_id", sa.CHAR(length=36), nullable=True),
        sa.Column("tipo", sa.String(length=20), nullable=False, server_default="pago"),
        sa.Column("email_destinatario", sa.String(length=255), nullable=False),
        sa.Column("alumno_nombre", sa.String(length=255), nullable=True),
        sa.Column("asunto", sa.String(length=255), nullable=False),
        sa.Column("mensaje", sa.String(length=500), nullable=False),
        sa.Column("estado", sa.String(length=50), nullable=False, server_default="simulado"),
        sa.Column("error_detalle", sa.Text(), nullable=True),
        sa.Column("enviado_en", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["pago_cuota_id"], ["pagos_cuotas.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute(
        "INSERT INTO notificaciones_email_v2 "
        "(id, pago_cuota_id, tipo, email_destinatario, alumno_nombre, asunto, mensaje, estado, error_detalle, enviado_en) "
        "SELECT id, pago_cuota_id, tipo, email_destinatario, NULL, asunto, mensaje, estado, NULL, enviado_en "
        "FROM notificaciones_email"
    )
    op.drop_table("notificaciones_email")
    op.rename_table("notificaciones_email_v2", "notificaciones_email")


def downgrade() -> None:
    op.drop_table("usuarios")

    op.create_table(
        "notificaciones_email_v1",
        sa.Column("id", sa.CHAR(length=36), nullable=False),
        sa.Column("pago_cuota_id", sa.CHAR(length=36), nullable=True),
        sa.Column("tipo", sa.String(length=20), nullable=False, server_default="pago"),
        sa.Column("email_destinatario", sa.String(length=255), nullable=False),
        sa.Column("asunto", sa.String(length=255), nullable=False),
        sa.Column("mensaje", sa.String(length=500), nullable=False),
        sa.Column("estado", sa.String(length=50), nullable=False, server_default="simulado"),
        sa.Column("enviado_en", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["pago_cuota_id"], ["pagos_cuotas.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute(
        "INSERT INTO notificaciones_email_v1 "
        "(id, pago_cuota_id, tipo, email_destinatario, asunto, mensaje, estado, enviado_en) "
        "SELECT id, pago_cuota_id, tipo, email_destinatario, asunto, mensaje, estado, enviado_en "
        "FROM notificaciones_email"
    )
    op.drop_table("notificaciones_email")
    op.rename_table("notificaciones_email_v1", "notificaciones_email")
