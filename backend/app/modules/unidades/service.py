from app.modules.unidades.repository import UnidadeRepository


class UnidadeService:
    def __init__(self, repo: UnidadeRepository):
        self.repo = repo
