"""initial

Revision ID: 0001_initial
Revises:
Create Date: 2026-01-21
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "perfil_acesso",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("descricao", sa.String(length=100), nullable=False),
    )
    op.create_index("ix_perfil_acesso_descricao", "perfil_acesso", ["descricao"], unique=True)

    op.create_table(
        "profissional",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nome", sa.String(length=200), nullable=False),
        sa.Column("perfil_acesso_id", sa.Integer(), sa.ForeignKey("perfil_acesso.id"), nullable=False),
        sa.Column("data_nascimento", sa.Date(), nullable=True),
        sa.Column("crefito", sa.String(length=50), nullable=True),
        sa.Column("criado_em", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_table(
        "usuario",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("senha_hash", sa.String(length=255), nullable=False),
        sa.Column("profissional_id", sa.Integer(), sa.ForeignKey("profissional.id"), nullable=True),
        sa.Column("perfil_acesso_id", sa.Integer(), sa.ForeignKey("perfil_acesso.id"), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("criado_em", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_usuario_email", "usuario", ["email"], unique=True)

    op.create_table(
        "unidade",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nome", sa.String(length=200), nullable=False),
        sa.Column("ocupacao_max", sa.Integer(), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("criado_em", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_table(
        "termo_uso",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("descricao", sa.Text(), nullable=False),
        sa.Column("versao", sa.String(length=50), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("criado_em", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_table(
        "aluno",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nome", sa.String(length=200), nullable=False),
        sa.Column("cpf", sa.String(length=14), nullable=False),
        sa.Column("rg", sa.String(length=20), nullable=True),
        sa.Column("unidade_id", sa.Integer(), sa.ForeignKey("unidade.id"), nullable=False),
        sa.Column("termo_uso_id", sa.Integer(), sa.ForeignKey("termo_uso.id"), nullable=True),
        sa.Column("criado_em", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("status", sa.Enum("ativo", "inativo", name="alunostatus", native_enum=False), nullable=False),
        sa.Column("observacoes", sa.Text(), nullable=True),
    )
    op.create_index("ix_aluno_cpf", "aluno", ["cpf"], unique=True)

    op.create_table(
        "endereco_aluno",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("aluno_id", sa.Integer(), sa.ForeignKey("aluno.id"), nullable=False),
        sa.Column("logradouro", sa.String(length=200), nullable=False),
        sa.Column("numero", sa.String(length=20), nullable=False),
        sa.Column("cep", sa.String(length=10), nullable=False),
        sa.Column("cidade", sa.String(length=100), nullable=False),
        sa.Column("bairro", sa.String(length=100), nullable=False),
        sa.Column("principal", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("criado_em", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_table(
        "recorrencia",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("descricao", sa.String(length=100), nullable=False),
        sa.Column("intervalo_meses", sa.Integer(), nullable=False),
    )

    op.create_table(
        "tipo_plano",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("descricao", sa.String(length=100), nullable=False),
        sa.Column("recorrencia_id", sa.Integer(), sa.ForeignKey("recorrencia.id"), nullable=False),
    )

    op.create_table(
        "tipo_servico",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("descricao", sa.String(length=100), nullable=False),
    )

    op.create_table(
        "plano",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("descricao", sa.String(length=200), nullable=False),
        sa.Column("tipo_plano_id", sa.Integer(), sa.ForeignKey("tipo_plano.id"), nullable=False),
        sa.Column("tipo_servico_id", sa.Integer(), sa.ForeignKey("tipo_servico.id"), nullable=False),
        sa.Column("preco", sa.Numeric(10, 2), nullable=False),
        sa.Column("quantidade_aulas", sa.Integer(), nullable=True),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("criado_em", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_table(
        "contrato",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("aluno_id", sa.Integer(), sa.ForeignKey("aluno.id"), nullable=False),
        sa.Column("plano_id", sa.Integer(), sa.ForeignKey("plano.id"), nullable=False),
        sa.Column("unidade_id", sa.Integer(), sa.ForeignKey("unidade.id"), nullable=False),
        sa.Column("tipo_plano_id", sa.Integer(), sa.ForeignKey("tipo_plano.id"), nullable=True),
        sa.Column("profissional_id", sa.Integer(), sa.ForeignKey("profissional.id"), nullable=True),
        sa.Column("criado_em", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("inicio", sa.Date(), nullable=False),
        sa.Column("fim", sa.Date(), nullable=True),
        sa.Column("status", sa.Enum("ativo", "pausado", "encerrado", name="contratostatus", native_enum=False), nullable=False),
        sa.Column("observacoes", sa.Text(), nullable=True),
    )

    op.create_table(
        "fornecedor",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nome", sa.String(length=200), nullable=False),
        sa.Column("documento", sa.String(length=20), nullable=True),
        sa.Column("whatsapp", sa.String(length=20), nullable=True),
    )

    op.create_table(
        "categoria",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("descricao", sa.String(length=100), nullable=False),
    )

    op.create_table(
        "subcategoria",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("categoria_id", sa.Integer(), sa.ForeignKey("categoria.id"), nullable=False),
        sa.Column("descricao", sa.String(length=100), nullable=False),
    )

    op.create_table(
        "contas_pagar",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("fornecedor_id", sa.Integer(), sa.ForeignKey("fornecedor.id"), nullable=False),
        sa.Column("categoria_id", sa.Integer(), sa.ForeignKey("categoria.id"), nullable=False),
        sa.Column("subcategoria_id", sa.Integer(), sa.ForeignKey("subcategoria.id"), nullable=True),
        sa.Column("vencimento", sa.Date(), nullable=False),
        sa.Column("criado_em", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("valor", sa.Numeric(10, 2), nullable=False),
        sa.Column("status", sa.Enum("aberto", "pago", "vencido", "cancelado", name="contastatus", native_enum=False), nullable=False),
        sa.Column("pago_em", sa.Date(), nullable=True),
        sa.Column("forma_pagamento", sa.String(length=50), nullable=True),
        sa.Column("observacao", sa.Text(), nullable=True),
    )

    op.create_table(
        "contas_receber",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("aluno_id", sa.Integer(), sa.ForeignKey("aluno.id"), nullable=False),
        sa.Column("contrato_id", sa.Integer(), sa.ForeignKey("contrato.id"), nullable=True),
        sa.Column("vencimento", sa.Date(), nullable=False),
        sa.Column("criado_em", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("valor", sa.Numeric(10, 2), nullable=False),
        sa.Column("status", sa.Enum("aberto", "pago", "vencido", "cancelado", name="contastatus", native_enum=False), nullable=False),
        sa.Column("recebido_em", sa.Date(), nullable=True),
        sa.Column("forma_pagamento", sa.String(length=50), nullable=True),
        sa.Column("observacao", sa.Text(), nullable=True),
        sa.Column("origem", sa.String(length=50), nullable=True),
    )

    op.create_table(
        "sala",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("unidade_id", sa.Integer(), sa.ForeignKey("unidade.id"), nullable=False),
        sa.Column("nome", sa.String(length=100), nullable=False),
    )

    op.create_table(
        "agenda_evento",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("unidade_id", sa.Integer(), sa.ForeignKey("unidade.id"), nullable=False),
        sa.Column("profissional_id", sa.Integer(), sa.ForeignKey("profissional.id"), nullable=False),
        sa.Column("sala_id", sa.Integer(), sa.ForeignKey("sala.id"), nullable=True),
        sa.Column("tipo_servico_id", sa.Integer(), sa.ForeignKey("tipo_servico.id"), nullable=False),
        sa.Column("inicio_datetime", sa.DateTime(), nullable=False),
        sa.Column("fim_datetime", sa.DateTime(), nullable=False),
        sa.Column("capacidade", sa.Integer(), nullable=False),
        sa.Column("status", sa.Enum("marcado", "confirmado", "cancelado", "no_show", "concluido", name="eventostatus", native_enum=False), nullable=False),
        sa.Column("criado_em", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("observacao", sa.Text(), nullable=True),
    )

    op.create_table(
        "totalpass_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("request_payload", sa.Text(), nullable=True),
        sa.Column("response_payload", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("criado_em", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_table(
        "whatsapp_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("to", sa.String(length=30), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("response_payload", sa.Text(), nullable=True),
        sa.Column("criado_em", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_table(
        "agenda_participante",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("evento_id", sa.Integer(), sa.ForeignKey("agenda_evento.id"), nullable=False),
        sa.Column("aluno_id", sa.Integer(), sa.ForeignKey("aluno.id"), nullable=False),
        sa.Column("status", sa.Enum("reservado", "confirmado", "cancelado", "presente", "no_show", name="participantestatus", native_enum=False), nullable=False),
        sa.Column("origem", sa.String(length=50), nullable=True),
        sa.Column("checkin_totalpass_id", sa.Integer(), sa.ForeignKey("totalpass_log.id"), nullable=True),
        sa.Column("criado_em", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_table(
        "agenda_recorrencia",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("aluno_id", sa.Integer(), sa.ForeignKey("aluno.id"), nullable=False),
        sa.Column("profissional_id", sa.Integer(), sa.ForeignKey("profissional.id"), nullable=False),
        sa.Column("unidade_id", sa.Integer(), sa.ForeignKey("unidade.id"), nullable=False),
        sa.Column("tipo_servico_id", sa.Integer(), sa.ForeignKey("tipo_servico.id"), nullable=False),
        sa.Column("regra_rrule", sa.String(length=200), nullable=True),
        sa.Column("inicio", sa.DateTime(), nullable=False),
        sa.Column("fim", sa.DateTime(), nullable=True),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )


def downgrade() -> None:
    op.drop_table("agenda_recorrencia")
    op.drop_table("agenda_participante")
    op.drop_table("whatsapp_log")
    op.drop_table("totalpass_log")
    op.drop_table("agenda_evento")
    op.drop_table("sala")
    op.drop_table("contas_receber")
    op.drop_table("contas_pagar")
    op.drop_table("subcategoria")
    op.drop_table("categoria")
    op.drop_table("fornecedor")
    op.drop_table("contrato")
    op.drop_table("plano")
    op.drop_table("tipo_servico")
    op.drop_table("tipo_plano")
    op.drop_table("recorrencia")
    op.drop_table("endereco_aluno")
    op.drop_table("aluno")
    op.drop_table("termo_uso")
    op.drop_table("unidade")
    op.drop_table("usuario")
    op.drop_table("profissional")
    op.drop_table("perfil_acesso")
