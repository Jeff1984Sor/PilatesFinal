from datetime import datetime
from pathlib import Path

from fastapi import HTTPException, status

from app.core.config import settings
from app.modules.alunos.repository import AlunoRepository, EnderecoRepository, AlunoAnexoRepository
from app.modules.alunos.models import EnderecoAluno
from app.modules.termos.repository import TermoRepository
from app.modules.termos.service import TermoRenderer
from app.shared.utils import normalize_cpf


class AlunoService:
    def __init__(self, repo: AlunoRepository, endereco_repo: EnderecoRepository):
        self.repo = repo
        self.endereco_repo = endereco_repo

    def create(self, data: dict):
        data["cpf"] = normalize_cpf(data["cpf"])
        if self.repo.get_by_cpf(data["cpf"]):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="CPF already registered")
        return self.repo.create(data)

    def add_endereco(self, aluno_id: int, data: dict):
        if data.get("principal"):
            self._clear_principal(aluno_id)
        data["aluno_id"] = aluno_id
        return self.endereco_repo.create(data)

    def _clear_principal(self, aluno_id: int):
        items, _ = self.endereco_repo.list(filters=[EnderecoAluno.aluno_id == aluno_id])
        for item in items:
            if item.principal:
                self.endereco_repo.update(item, {"principal": False})


class AlunoAnexoService:
    def __init__(
        self,
        repo: AlunoRepository,
        anexo_repo: AlunoAnexoRepository,
        termo_repo: TermoRepository,
        renderer: TermoRenderer,
    ):
        self.repo = repo
        self.anexo_repo = anexo_repo
        self.termo_repo = termo_repo
        self.renderer = renderer

    def create_termo_pdf(self, aluno_id: int, termo_id: int | None, contrato_id: int | None):
        aluno = self.repo.get(aluno_id)
        if not aluno:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aluno not found")

        termo = self.termo_repo.get(termo_id) if termo_id else self.termo_repo.get_active()
        if not termo:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active termo found")

        context = self.renderer.build_context(aluno_id=aluno_id, contrato_id=contrato_id)
        rendered_text = self.renderer.render(termo.descricao, context)
        pdf_bytes = self.renderer.generate_pdf(rendered_text)

        storage_dir = Path(settings.STORAGE_DIR) / "termos"
        storage_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        file_name = f"termo_uso_{aluno_id}_{stamp}.pdf"
        file_path = storage_dir / file_name
        file_path.write_bytes(pdf_bytes)

        return self.anexo_repo.create(
            {
                "aluno_id": aluno_id,
                "termo_uso_id": termo.id,
                "contrato_id": contrato_id,
                "tipo": "termo_uso",
                "arquivo_nome": file_name,
                "arquivo_path": str(file_path),
                "mime_type": "application/pdf",
            }
        )
