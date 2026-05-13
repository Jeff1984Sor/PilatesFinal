import json
import re
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
    if not GEMINI_API_KEY:
        raise GeminiError("GEMINI_API_KEY nao configurado")
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = (
        "Melhore a evolucao abaixo em portugues do Brasil, mantendo somente os fatos informados, "
        "sem inventar sintomas, condutas, diagnosticos ou exercicios. "
        "Deixe claro, profissional e objetivo para prontuario. "
        "Retorne apenas o texto final, sem markdown.\n\n"
        f"{texto}"
    )
    try:
        response = model.generate_content(prompt)
    except Exception as exc:
        raise GeminiError(f"Falha na chamada da IA: {exc}") from exc
    clean_text = re.sub(r"^```(?:text|markdown)?|```$", "", (response.text or "").strip()).strip()
    if not clean_text:
        raise GeminiError("A IA retornou resposta vazia")
    return {"texto": clean_text}
