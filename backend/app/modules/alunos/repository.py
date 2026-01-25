from sqlalchemy.orm import Session
from sqlalchemy import select

from app.shared.repository import BaseRepository
from app.modules.alunos.models import Aluno, EnderecoAluno, AlunoAnexo


class AlunoRepository(BaseRepository[Aluno]):
    def __init__(self, db: Session):
        super().__init__(db, Aluno)

    def get_by_cpf(self, cpf: str):
        return self.db.execute(select(Aluno).where(Aluno.cpf == cpf)).scalar_one_or_none()


class EnderecoRepository(BaseRepository[EnderecoAluno]):
    def __init__(self, db: Session):
        super().__init__(db, EnderecoAluno)


class AlunoAnexoRepository(BaseRepository[AlunoAnexo]):
    def __init__(self, db: Session):
        super().__init__(db, AlunoAnexo)
