from datetime import date, datetime, timedelta

import pytest
from sqlalchemy import delete, select

from app.core.database import SessionLocal
from app.modules.aulas.models import Aula, AulaAluno
from app.modules.contratos.models import Contrato
from app.modules.contratos.service import ContratoService
from app.modules.contratos.schemas import ContratoCreate
from app.modules.contratos.scheduler import TZ, daily_slots
from app.modules.planos.models import Recorrencia, TipoPlano, TipoServico, Plano
from app.modules.unidades.models import Unidade
from app.modules.alunos.models import Aluno
from fastapi import HTTPException


@pytest.fixture()
def db_session():
    db = SessionLocal()
    yield db
    db.rollback()
    for model in [AulaAluno, Aula, Contrato, Aluno, Plano, TipoPlano, Recorrencia, TipoServico, Unidade]:
        db.execute(delete(model))
    db.commit()
    db.close()


def seed_base(db, *, capacidade=5, aulas_por_semana=2, duracao_meses=1):
    unidade = Unidade(nome=f"Unidade {capacidade}", ocupacao_max=capacidade, ativo=True)
    db.add(unidade)
    db.flush()

    recorrencia = Recorrencia(descricao="Mensal", intervalo_meses=duracao_meses)
    db.add(recorrencia)
    db.flush()

    tipo_plano = TipoPlano(descricao="Padrao", recorrencia_id=recorrencia.id)
    db.add(tipo_plano)
    db.flush()

    tipo_servico = TipoServico(descricao="Pilates")
    db.add(tipo_servico)
    db.flush()

    plano = Plano(
        descricao="Plano",
        tipo_plano_id=tipo_plano.id,
        tipo_servico_id=tipo_servico.id,
        preco=100,
        quantidade_aulas=None,
        aulas_por_semana=aulas_por_semana,
        duracao_meses=duracao_meses,
        ativo=True,
    )
    db.add(plano)
    db.flush()

    aluno = Aluno(
        nome="Aluno Teste",
        cpf=f"000.000.000-{capacidade}{aulas_por_semana}",
        rg=None,
        unidade_id=unidade.id,
        termo_uso_id=None,
        status="ativo",
        observacoes=None,
    )
    db.add(aluno)
    db.flush()

    db.commit()
    return aluno, plano, unidade


def create_contract(db, aluno_id, plano_id, unidade_id, inicio):
    service = ContratoService(db)
    payload = ContratoCreate(
        aluno_id=aluno_id,
        plano_id=plano_id,
        unidade_id=unidade_id,
        tipo_plano_id=None,
        profissional_id=None,
        inicio=inicio,
        fim=None,
        status="ativo",
        observacoes=None,
    )
    return service.create_with_agenda(payload)


def test_daily_slots_friday_cutoff():
    friday = date(2026, 2, 6)
    slots = daily_slots(friday)
    assert len(slots) == 6
    assert slots[-1].time().hour == 11
    assert slots[-1].time().minute == 10


def test_distribution_2_por_semana(db_session):
    aluno, plano, unidade = seed_base(db_session, capacidade=5, aulas_por_semana=2, duracao_meses=1)
    inicio = date(2026, 2, 2)
    contrato = create_contract(db_session, aluno.id, plano.id, unidade.id, inicio)

    week_start = inicio
    week_end = week_start + timedelta(days=5)
    week_start_dt = datetime.combine(week_start, datetime.min.time(), tzinfo=TZ)
    week_end_dt = datetime.combine(week_end, datetime.min.time(), tzinfo=TZ)
    stmt = (
        select(Aula.inicio_datetime)
        .join(AulaAluno, AulaAluno.aula_id == Aula.id)
        .where(
            AulaAluno.contrato_id == contrato.id,
            Aula.inicio_datetime >= week_start_dt,
            Aula.inicio_datetime < week_end_dt,
        )
    )
    rows = db_session.execute(stmt).all()
    weekdays = {row[0].weekday() for row in rows}
    assert weekdays == {0, 2}


def test_distribution_3_por_semana(db_session):
    aluno, plano, unidade = seed_base(db_session, capacidade=5, aulas_por_semana=3, duracao_meses=1)
    inicio = date(2026, 2, 2)
    contrato = create_contract(db_session, aluno.id, plano.id, unidade.id, inicio)

    week_start = inicio
    week_end = week_start + timedelta(days=5)
    week_start_dt = datetime.combine(week_start, datetime.min.time(), tzinfo=TZ)
    week_end_dt = datetime.combine(week_end, datetime.min.time(), tzinfo=TZ)
    stmt = (
        select(Aula.inicio_datetime)
        .join(AulaAluno, AulaAluno.aula_id == Aula.id)
        .where(
            AulaAluno.contrato_id == contrato.id,
            Aula.inicio_datetime >= week_start_dt,
            Aula.inicio_datetime < week_end_dt,
        )
    )
    rows = db_session.execute(stmt).all()
    weekdays = {row[0].weekday() for row in rows}
    assert weekdays == {0, 2, 4}


def test_distribution_5_por_semana(db_session):
    aluno, plano, unidade = seed_base(db_session, capacidade=5, aulas_por_semana=5, duracao_meses=1)
    inicio = date(2026, 2, 2)
    contrato = create_contract(db_session, aluno.id, plano.id, unidade.id, inicio)

    week_start = inicio
    week_end = week_start + timedelta(days=5)
    week_start_dt = datetime.combine(week_start, datetime.min.time(), tzinfo=TZ)
    week_end_dt = datetime.combine(week_end, datetime.min.time(), tzinfo=TZ)
    stmt = (
        select(Aula.inicio_datetime)
        .join(AulaAluno, AulaAluno.aula_id == Aula.id)
        .where(
            AulaAluno.contrato_id == contrato.id,
            Aula.inicio_datetime >= week_start_dt,
            Aula.inicio_datetime < week_end_dt,
        )
    )
    rows = db_session.execute(stmt).all()
    weekdays = {row[0].weekday() for row in rows}
    assert weekdays == {0, 1, 2, 3, 4}


def test_capacity_limit(db_session):
    aluno1, plano, unidade = seed_base(db_session, capacidade=1, aulas_por_semana=1, duracao_meses=1)
    aluno2 = Aluno(
        nome="Aluno 2",
        cpf="000.000.000-99",
        rg=None,
        unidade_id=unidade.id,
        termo_uso_id=None,
        status="ativo",
        observacoes=None,
    )
    db_session.add(aluno2)
    db_session.commit()

    inicio = date(2026, 2, 2)
    contrato1 = create_contract(db_session, aluno1.id, plano.id, unidade.id, inicio)
    contrato2 = create_contract(db_session, aluno2.id, plano.id, unidade.id, inicio)

    stmt = (
        select(Aula.id)
        .join(AulaAluno, AulaAluno.aula_id == Aula.id)
        .where(AulaAluno.contrato_id.in_([contrato1.id, contrato2.id]))
    )
    aula_ids = [row[0] for row in db_session.execute(stmt).all()]
    for aula_id in aula_ids:
        count = db_session.execute(select(AulaAluno).where(AulaAluno.aula_id == aula_id)).scalars().all()
        assert len(count) <= unidade.ocupacao_max


def test_idempotent_gerar_agenda(db_session):
    aluno, plano, unidade = seed_base(db_session, capacidade=5, aulas_por_semana=1, duracao_meses=1)
    inicio = date(2026, 2, 2)
    contrato = create_contract(db_session, aluno.id, plano.id, unidade.id, inicio)

    service = ContratoService(db_session)
    with pytest.raises(HTTPException):
        service.gerar_agenda(contrato.id)
