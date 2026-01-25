from app.modules.contratos.repository import ContratoRepository


class ContratoService:
    def __init__(self, repo: ContratoRepository):
        self.repo = repo
