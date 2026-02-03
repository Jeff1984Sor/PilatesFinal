"""agenda_contrato

Revision ID: 0004_agenda_contrato
Revises: 0003_contrato_modelo
Create Date: 2026-02-03
"""
from alembic import op
import sqlalchemy as sa

revision = "0004_agenda_contrato"
down_revision = "0003_contrato_modelo"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("plano", sa.Column("aulas_por_semana", sa.Integer(), nullable=True))
    op.add_column("plano", sa.Column("duracao_meses", sa.Integer(), nullable=True))

    op.add_column("contrato", sa.Column("agenda_gerada_em", sa.DateTime(timezone=True), nullable=True))
    op.add_column("contrato", sa.Column("idempotency_key", sa.String(length=100), nullable=True))
    op.create_index("ix_contrato_idempotency_key", "contrato", ["idempotency_key"], unique=True)

    op.create_table(
        "aula",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("unidade_id", sa.Integer(), sa.ForeignKey("unidade.id"), nullable=False),
        sa.Column("inicio_datetime", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fim_datetime", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.Enum("agendada", "cancelada", "concluida", name="aulastatus", native_enum=False), nullable=False),
        sa.Column("criado_em", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("unidade_id", "inicio_datetime", "fim_datetime", name="uq_aula_unidade_slot"),
    )

    op.create_table(
        "aula_aluno",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("aula_id", sa.Integer(), sa.ForeignKey("aula.id"), nullable=False),
        sa.Column("aluno_id", sa.Integer(), sa.ForeignKey("aluno.id"), nullable=False),
        sa.Column("contrato_id", sa.Integer(), sa.ForeignKey("contrato.id"), nullable=False),
        sa.Column("criado_em", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("aula_id", "aluno_id", name="uq_aula_aluno"),
    )


def downgrade() -> None:
    op.drop_table("aula_aluno")
    op.drop_table("aula")

    op.drop_index("ix_contrato_idempotency_key", table_name="contrato")
    op.drop_column("contrato", "idempotency_key")
    op.drop_column("contrato", "agenda_gerada_em")

    op.drop_column("plano", "duracao_meses")
    op.drop_column("plano", "aulas_por_semana")
