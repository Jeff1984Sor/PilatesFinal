"""add contrato_modelo

Revision ID: 0003_contrato_modelo
Revises: 0002_aluno_anexo
Create Date: 2026-01-22
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_contrato_modelo"
down_revision = "0002_aluno_anexo"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "contrato_modelo",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("titulo", sa.String(length=200), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("criado_em", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("atualizado_em", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
    )


def downgrade() -> None:
    op.drop_table("contrato_modelo")
