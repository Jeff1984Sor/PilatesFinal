from abc import ABC, abstractmethod


class TotalPassClient(ABC):
    @abstractmethod
    def validar_aluno(self, cpf: str) -> dict:
        raise NotImplementedError

    @abstractmethod
    def registrar_presenca(self, cpf: str, evento_id: int) -> dict:
        raise NotImplementedError
