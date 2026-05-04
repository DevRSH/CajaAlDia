"""Tablas iniciales: curso, movimiento, folio_secuencia."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001_inicial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "cursos",
        sa.Column("id", sa.CHAR(36), primary_key=True),
        sa.Column("codigo", sa.String(64), nullable=False),
        sa.Column("nombre", sa.String(255), nullable=False),
        sa.Column("colegio", sa.String(255), nullable=False),
        sa.Column("año", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("codigo", name="uq_cursos_codigo"),
    )
    op.create_table(
        "folio_secuencia",
        sa.Column("id", sa.CHAR(36), primary_key=True),
        sa.Column("curso_id", sa.CHAR(36), sa.ForeignKey("cursos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("año", sa.Integer(), nullable=False),
        sa.Column("ultimo_numero", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("curso_id", "año", name="uq_folio_seq_curso_año"),
    )
    op.create_table(
        "movimientos",
        sa.Column("id", sa.CHAR(36), primary_key=True),
        sa.Column("curso_id", sa.CHAR(36), sa.ForeignKey("cursos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tipo", sa.String(16), nullable=False),
        sa.Column("monto", sa.Integer(), nullable=False),
        sa.Column("descripcion", sa.String(200), nullable=False),
        sa.Column("folio", sa.String(64), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("anulado", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("folio", name="uq_movimientos_folio"),
    )
    op.create_index("ix_movimientos_curso_fecha", "movimientos", ["curso_id", "fecha"])


def downgrade() -> None:
    op.drop_index("ix_movimientos_curso_fecha", table_name="movimientos")
    op.drop_table("movimientos")
    op.drop_table("folio_secuencia")
    op.drop_table("cursos")
