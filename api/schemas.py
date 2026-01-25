from datetime import date
from pydantic import BaseModel


class AlunoIn(BaseModel):
    cdAluno: int
    dsNome: str
    dsCPF: str
    dsRg: str | None = None
    cdUnidade_id: int
    cdTermoUso_id: int | None = None


class AlunoOut(BaseModel):
    id: int
    cdAluno: int
    dsNome: str
    dsCPF: str
    dsRg: str | None = None

    class Config:
        from_attributes = True


class ContratoIn(BaseModel):
    cdContrato: int
    cdAluno_id: int
    cdPlano_id: int
    cdUnidade_id: int
    cdProfissional_id: int
    dtInicioContrato: date
    dtFimContrato: date
    valor: float

    def to_contrato_data(self):
        return {
            "cdContrato": self.cdContrato,
            "cdAluno_id": self.cdAluno_id,
            "cdPlano_id": self.cdPlano_id,
            "cdUnidade_id": self.cdUnidade_id,
            "cdProfissional_id": self.cdProfissional_id,
            "dtInicioContrato": self.dtInicioContrato,
            "dtFimContrato": self.dtFimContrato,
        }


class AulaSessaoIn(BaseModel):
    unidade_id: int
    tipoServico_id: int
    profissional_id: int | None = None
    data: date
    horaInicio: str
    horaFim: str
    capacidade: int | None = None


class ReservaIn(BaseModel):
    aluno_id: int
    aula_sessao_id: int
    status: str = "RESERVADA"
