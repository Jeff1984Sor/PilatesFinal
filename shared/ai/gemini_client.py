import json
import os
import re
import time
from typing import Dict
import google.generativeai as genai
from shared.config import GEMINI_API_KEY


class GeminiError(Exception):
    pass


GEMINI_MODEL_CANDIDATES = [
    os.getenv("GEMINI_MODEL", "").strip(),
    "gemini-3-flash-preview",
    "gemini-3-pro-preview",
    "gemini-2.0-flash",
    "gemini-2.5-flash",
    "gemini-flash-latest",
]


def _model_names():
    names = []
    for name in GEMINI_MODEL_CANDIDATES:
        if name and name not in names:
            names.append(name)
    return names


def _generate_content(prompt: str):
    if not GEMINI_API_KEY:
        raise GeminiError("GEMINI_API_KEY nao configurado")
    genai.configure(api_key=GEMINI_API_KEY)
    last_error = None
    for model_name in _model_names():
        try:
            model = genai.GenerativeModel(model_name)
            return model.generate_content(prompt)
        except Exception as exc:
            last_error = exc
            if "is not found" not in str(exc) and "not supported for generateContent" not in str(exc):
                break
    raise GeminiError(f"Falha na chamada da IA: {last_error}") from last_error


def _call_gemini(prompt: str) -> Dict:
    for attempt in range(3):
        try:
            response = _generate_content(prompt)
            response_text = (response.text or "").strip()
            if response_text.startswith("```"):
                response_text = response_text.strip("`").strip()
                if response_text.lower().startswith("json"):
                    response_text = response_text[4:].strip()
            if "{" in response_text and "}" in response_text:
                response_text = response_text[response_text.find("{") : response_text.rfind("}") + 1]
            data = json.loads(response_text)
            return data
        except Exception as exc:
            if attempt == 2:
                raise GeminiError("Falha ao processar resposta") from exc
            time.sleep(1)
    raise GeminiError("Falha ao processar resposta")


def extract_student_from_document(file_bytes: bytes, filename: str) -> Dict:
    prompt = (
        "Extraia nome, cpf, rg, data_nascimento de um documento. "
        "Responda somente JSON estrito com chaves nome, cpf, rg, data_nascimento."
    )
    return _call_gemini(prompt)


def extract_address_from_proof(file_bytes: bytes, filename: str) -> Dict:
    prompt = (
        "Extraia logradouro, numero, cep, cidade, bairro de um comprovante de endereco. "
        "Responda somente JSON estrito com chaves logradouro, numero, cep, cidade, bairro."
    )
    return _call_gemini(prompt)


def improve_evolution_text(texto: str) -> Dict:
    prompt = f"""
Voce e uma assistente de apoio clinico para um Studio de Pilates chamado Mayris Pilates.

A profissional responsavel e fisioterapeuta experiente e utiliza este campo para registrar a evolucao do aluno/paciente apos cada aula.

Sua tarefa e reescrever e enriquecer o texto informado, deixando-o mais claro, tecnico, organizado e adequado para registro de evolucao fisioterapeutica/pilates.

Regras obrigatorias:

1. Nao invente informacoes.
2. Nao crie diagnostico clinico.
3. Nao acrescente sintomas, condutas, exercicios, avaliacoes, testes ou orientacoes que nao estejam no texto original.
4. Nao afirme melhora, piora, limitacao funcional ou evolucao positiva/negativa se isso nao foi informado.
5. Corrija erros de portugues, digitacao e concordancia.
6. Transforme frases muito informais em linguagem profissional.
7. Mantenha o texto objetivo, humanizado e util para acompanhamento futuro.
8. Preserve todas as informacoes relevantes do texto original.
9. Caso o texto original seja curto, apenas melhore a redacao sem aumentar demais.
10. Caso haja relato de dor, registre a localizacao e a queixa de forma clara.
11. Nao use bullets, listas ou titulos, a menos que o texto original seja muito longo.
12. Nao escreva explicacoes sobre o que voce fez. Retorne apenas o texto final enriquecido.

Tom desejado:
- Profissional
- Clinico
- Claro
- Humano
- Objetivo
- Adequado para prontuario/evolucao de aula

Texto original:
"{texto}"

Retorne apenas a evolucao enriquecida:
""".strip()
    try:
        response = _generate_content(prompt)
    except GeminiError:
        raise
    clean_text = re.sub(r"^```(?:text|markdown)?|```$", "", (response.text or "").strip()).strip()
    if not clean_text:
        raise GeminiError("A IA retornou resposta vazia")
    return {"texto": clean_text}
