from datetime import date, datetime, time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.database import SessionLocal
from app.main import app


def _setup_core_tables(db):
    db.execute(text('CREATE TABLE IF NOT EXISTS core_unidade (id INTEGER PRIMARY KEY, "dsUnidade" TEXT)'))
    db.execute(text('CREATE TABLE IF NOT EXISTS core_profissional (id INTEGER PRIMARY KEY, profissional TEXT)'))
    db.execute(text('CREATE TABLE IF NOT EXISTS core_aluno (id INTEGER PRIMARY KEY, "dsNome" TEXT, "dsCPF" TEXT, foto TEXT, autoriza_imagem INTEGER DEFAULT 0, termo_aceite_em DATETIME)'))
    db.execute(text('CREATE TABLE IF NOT EXISTS core_telefonealuno (id INTEGER PRIMARY KEY, "cdAluno_id" INTEGER, "dsTelefone" TEXT, "dtCadastro" DATETIME)'))
    db.execute(text('CREATE TABLE IF NOT EXISTS core_plano (id INTEGER PRIMARY KEY, "dsPlano" TEXT)'))
    db.execute(text('CREATE TABLE IF NOT EXISTS core_contrato (id INTEGER PRIMARY KEY, "cdAluno_id" INTEGER, "cdPlano_id" INTEGER, "dtInicioContrato" DATE, "dtFimContrato" DATE, status TEXT)'))
    db.execute(text('CREATE TABLE IF NOT EXISTS core_aulasessao (id INTEGER PRIMARY KEY, unidade_id INTEGER, profissional_id INTEGER, data DATE, "horaInicio" TIME, "horaFim" TIME)'))
    db.execute(text('CREATE TABLE IF NOT EXISTS core_reserva (id INTEGER PRIMARY KEY, aluno_id INTEGER, "aulaSessao_id" INTEGER, status TEXT)'))
    db.execute(text('CREATE TABLE IF NOT EXISTS core_contasreceber (id INTEGER PRIMARY KEY, contrato_id INTEGER, status TEXT)'))
    db.execute(text('CREATE TABLE IF NOT EXISTS core_evolucaoaluno (id INTEGER PRIMARY KEY, reserva_id INTEGER, profissional_id INTEGER, texto TEXT, "dtEvolucao" DATETIME)'))
    db.commit()


def _cleanup_core_tables(db):
    tables = [
        "core_evolucaoaluno",
        "core_contasreceber",
        "core_reserva",
        "core_aulasessao",
        "core_contrato",
        "core_plano",
        "core_telefonealuno",
        "core_aluno",
        "core_profissional",
        "core_unidade",
    ]
    for table in tables:
        db.execute(text(f"DELETE FROM {table}"))
    db.commit()


@pytest.fixture()
def db_session():
    db = SessionLocal()
    _setup_core_tables(db)
    yield db
    _cleanup_core_tables(db)
    db.close()


@pytest.fixture()
def client():
    return TestClient(app)


def seed_operacao(db):
    db.execute(text('INSERT INTO core_unidade (id, "dsUnidade") VALUES (1, "Unidade Central")'))
    db.execute(text('INSERT INTO core_profissional (id, profissional) VALUES (1, "Flavia Barros")'))
    db.execute(text('INSERT INTO core_aluno (id, "dsNome", "dsCPF", foto, autoriza_imagem, termo_aceite_em) VALUES (1, "Elena Vianna", "123", NULL, 0, CURRENT_TIMESTAMP)'))
    db.execute(text('INSERT INTO core_telefonealuno (id, "cdAluno_id", "dsTelefone", "dtCadastro") VALUES (1, 1, "11999998888", CURRENT_TIMESTAMP)'))
    db.execute(text('INSERT INTO core_plano (id, "dsPlano") VALUES (1, "Pilates 2x semana")'))
    db.execute(text('INSERT INTO core_contrato (id, "cdAluno_id", "cdPlano_id", "dtInicioContrato", "dtFimContrato", status) VALUES (1, 1, 1, "2026-02-01", "2026-03-01", "ASSINADO")'))
    db.execute(text('INSERT INTO core_aulasessao (id, unidade_id, profissional_id, data, "horaInicio", "horaFim") VALUES (1, 1, 1, "2026-02-03", "07:00", "07:50")'))
    db.execute(text('INSERT INTO core_reserva (id, aluno_id, "aulaSessao_id", status) VALUES (1, 1, 1, "RESERVADA")'))
    db.execute(text('INSERT INTO core_contasreceber (id, contrato_id, status) VALUES (1, 1, "ABERTO")'))
    db.commit()


def test_listagem_operacao_filtra_por_data(client, db_session):
    seed_operacao(db_session)
    resp = client.get("/aulas/operacao", params={"data": "2026-02-03"})
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["total"] == 1
    item = payload["items"][0]
    assert item["aluno"]["nome"] == "Elena Vianna"
    assert item["plano"]["descricao"] == "Pilates 2x semana"
    assert item["flags"]["cobranca_pendente"] is True


def test_salvar_evolucao_e_finalizar(client, db_session):
    seed_operacao(db_session)
    resp = client.post(
        "/aulas/1/evolucoes",
        json={"texto": "Boa sessao", "profissional_id": 1, "finalizar": True},
    )
    assert resp.status_code == 200
    status_row = db_session.execute(text('SELECT status FROM core_reserva WHERE id = 1')).first()
    assert status_row[0] == "CONCLUIDA"


def test_status_update_faltou(client, db_session):
    seed_operacao(db_session)
    resp = client.patch("/aulas/1/status", json={"acao": "faltou"})
    assert resp.status_code == 200
    status_row = db_session.execute(text('SELECT status FROM core_reserva WHERE id = 1')).first()
    assert status_row[0] == "FALTOU_SEM_AVISAR"
