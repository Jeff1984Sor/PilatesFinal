from fastapi import HTTPException, status

from app.modules.profissionais.repository import ProfissionalRepository


class ProfissionalService:
    def __init__(self, repo: ProfissionalRepository):
        self.repo = repo

    def get_or_404(self, profissional_id: int):
        profissional = self.repo.get(profissional_id)
        if not profissional:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profissional not found")
        return profissional
