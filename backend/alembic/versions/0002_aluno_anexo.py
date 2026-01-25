"""add aluno_anexo

Revision ID: 0002_aluno_anexo
Revises: 0001_initial
Create Date: 2026-01-22
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_aluno_anexo"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "aluno_anexo",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("aluno_id", sa.Integer(), sa.ForeignKey("aluno.id"), nullable=False),
        sa.Column("termo_uso_id", sa.Integer(), sa.ForeignKey("termo_uso.id"), nullable=True),
        sa.Column("contrato_id", sa.Integer(), sa.ForeignKey("contrato.id"), nullable=True),
        sa.Column("tipo", sa.String(length=50), nullable=False),
        sa.Column("arquivo_nome", sa.String(length=255), nullable=False),
        sa.Column("arquivo_path", sa.String(length=500), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("criado_em", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_aluno_anexo_aluno_id", "aluno_anexo", ["aluno_id"])


def downgrade() -> None:
    op.drop_index("ix_aluno_anexo_aluno_id", table_name="aluno_anexo")
    op.drop_table("aluno_anexo")
