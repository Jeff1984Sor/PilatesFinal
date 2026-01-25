import re


def normalize_cpf(cpf: str) -> str:
    return re.sub(r"\D", "", cpf or "")
