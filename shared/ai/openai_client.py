import base64
import json
import re
import time
from typing import Dict

from openai import OpenAI

from shared.config import OPENAI_API_KEY, OPENAI_MODEL


class AIError(Exception):
    pass


# Compatibilidade: o codigo antigo importa/captura GeminiError.
GeminiError = AIError


_client = None


def _get_client() -> OpenAI:
    global _client
    if not OPENAI_API_KEY:
        raise AIError("OPENAI_API_KEY nao configurado")
    if _client is None:
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


def _guess_mime(filename: str | None) -> str | None:
    ext = (filename or "").lower().rsplit(".", 1)[-1] if filename and "." in filename else ""
    return {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "webp": "image/webp",
        "gif": "image/gif",
    }.get(ext)


def _chat(prompt: str, *, images: list[tuple[bytes, str]] | None = None) -> str:
    """Chama o chat da OpenAI e devolve o texto da resposta. `images` e uma lista
    de (bytes, mime) para leitura de documentos via visao."""
    client = _get_client()
    content: list[dict] = [{"type": "text", "text": prompt}]
    for file_bytes, mime in images or []:
        b64 = base64.b64encode(file_bytes).decode("ascii")
        content.append(
            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}}
        )
    last_error = None
    for attempt in range(3):
        try:
            resp = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": content}],
                temperature=0.3,
            )
            return (resp.choices[0].message.content or "").strip()
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt < 2:
                time.sleep(1)
    raise AIError(f"Falha na chamada da IA: {last_error}") from last_error


def _parse_json(response_text: str) -> Dict:
    text = (response_text or "").strip()
    if text.startswith("```"):
        text = text.strip("`").strip()
        if text.lower().startswith("json"):
            text = text[4:].strip()
    if "{" in text and "}" in text:
        text = text[text.find("{") : text.rfind("}") + 1]
    try:
        return json.loads(text)
    except Exception as exc:  # noqa: BLE001
        raise AIError("Falha ao processar resposta") from exc


def extract_student_from_document(file_bytes: bytes, filename: str) -> Dict:
    prompt = (
        "Extraia nome, cpf, rg, data_nascimento do documento enviado. "
        "Responda somente JSON estrito com chaves nome, cpf, rg, data_nascimento."
    )
    mime = _guess_mime(filename)
    images = [(file_bytes, mime)] if mime else None
    return _parse_json(_chat(prompt, images=images))


def extract_address_from_proof(file_bytes: bytes, filename: str) -> Dict:
    prompt = (
        "Extraia logradouro, numero, cep, cidade, bairro do comprovante de endereco enviado. "
        "Responda somente JSON estrito com chaves logradouro, numero, cep, cidade, bairro."
    )
    mime = _guess_mime(filename)
    images = [(file_bytes, mime)] if mime else None
    return _parse_json(_chat(prompt, images=images))


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
    response_text = _chat(prompt)
    clean_text = re.sub(r"^```(?:text|markdown)?|```$", "", response_text.strip()).strip()
    if not clean_text:
        raise AIError("A IA retornou resposta vazia")
    return {"texto": clean_text}
