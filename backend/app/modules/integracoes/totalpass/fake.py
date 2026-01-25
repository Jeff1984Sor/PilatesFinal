from app.modules.integracoes.totalpass.port import TotalPassClient


class FakeTotalPassClient(TotalPassClient):
    def validar_aluno(self, cpf: str) -> dict:
        return {"cpf": cpf, "elegivel": True, "plano": "mock"}

    def registrar_presenca(self, cpf: str, evento_id: int) -> dict:
        return {"cpf": cpf, "evento_id": evento_id, "status": "ok"}
