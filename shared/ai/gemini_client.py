import json
import time
from typing import Dict
import google.generativeai as genai
from shared.config import GEMINI_API_KEY


class GeminiError(Exception):
    pass


def _call_gemini(prompt: str) -> Dict:
    if not GEMINI_API_KEY:
        raise GeminiError("GEMINI_API_KEY nao configurado")
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
    for attempt in range(3):
        try:
            response = model.generate_content(prompt)
            data = json.loads(response.text)
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
