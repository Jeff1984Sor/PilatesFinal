"""comissao

Revision ID: 0005_comissao
Revises: 0004_agenda_contrato
Create Date: 2026-06-05
"""
from alembic import op
import sqlalchemy as sa

revision = "0005_comissao"
down_revision = "0004_agenda_contrato"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("profissional", sa.Column("comissao_percentual", sa.Numeric(5, 2), nullable=True))
    op.add_column(
        "contas_receber",
        sa.Column("profissional_id", sa.Integer(), sa.ForeignKey("profissional.id"), nullable=True),
    )

    op.create_table(
        "comissao",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("profissional_id", sa.Integer(), sa.ForeignKey("profissional.id"), nullable=False),
        sa.Column("conta_receber_id", sa.Integer(), sa.ForeignKey("contas_receber.id"), nullable=True),
        sa.Column("contrato_id", sa.Integer(), sa.ForeignKey("contrato.id"), nullable=True),
        sa.Column("competencia", sa.Date(), nullable=False),
        sa.Column("valor_base", sa.Numeric(10, 2), nullable=False),
        sa.Column("percentual", sa.Numeric(5, 2), nullable=False),
        sa.Column("valor", sa.Numeric(10, 2), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pendente", "pago", name="comissaostatus", native_enum=False),
            nullable=False,
        ),
        sa.Column("pago_em", sa.Date(), nullable=True),
        sa.Column("criado_em", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("conta_receber_id", name="uq_comissao_conta_receber"),
    )


def downgrade() -> None:
    op.drop_table("comissao")
    op.drop_column("contas_receber", "profissional_id")
    op.drop_column("profissional", "comissao_percentual")
