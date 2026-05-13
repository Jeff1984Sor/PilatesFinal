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
    prompt = (
        "Voce e um assistente de fisioterapia/Pilates. Melhore a evolucao abaixo em portugues do Brasil, "
        "mantendo os fatos informados, sem inventar sintomas, condutas ou diagnosticos. "
        "Deixe o texto claro, profissional, objetivo e pronto para prontuario. "
        "Responda somente JSON estrito com a chave texto.\n\n"
        f"Evolucao original:\n{texto}"
    )
    try:
        return _call_gemini(prompt)
    except GeminiError:
        if not GEMINI_API_KEY:
            raise
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")
        fallback_prompt = (
            "Melhore a evolucao abaixo em portugues do Brasil, mantendo somente os fatos informados, "
            "sem inventar dados. Retorne apenas o texto final, sem markdown.\n\n"
            f"{texto}"
        )
        response = model.generate_content(fallback_prompt)
        clean_text = re.sub(r"^```(?:text|markdown)?|```$", "", (response.text or "").strip()).strip()
        if not clean_text:
            raise GeminiError("Falha ao processar resposta")
        return {"texto": clean_text}
