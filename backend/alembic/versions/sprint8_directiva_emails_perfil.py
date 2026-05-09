"""Sprint 8: emails directiva en cursos y perfil usuario

Revision ID: sprint8_directiva_emails
Revises: sprint7_usuarios
Create Date: 2026-05-09 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "sprint8_directiva_emails"
down_revision: Union[str, None] = "sprint7_usuarios"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Emails de directiva en cursos
    op.add_column("cursos", sa.Column("directiva_tesorera_email", sa.String(length=255), nullable=True))
    op.add_column("cursos", sa.Column("directiva_presidenta_email", sa.String(length=255), nullable=True))
    op.add_column("cursos", sa.Column("directiva_secretaria_email", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("cursos", "directiva_secretaria_email")
    op.drop_column("cursos", "directiva_presidenta_email")
    op.drop_column("cursos", "directiva_tesorera_email")
