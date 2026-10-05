"""Acesso restrito para o perfil de professor.

Quem tem perfil de acesso com "professor" no nome so enxerga a agenda e as proprias aulas
(evolucao e avaliacao dos alunos dessas aulas). Tudo o mais -- financeiro, contratos,
cadastros, configuracoes, lista geral de alunos -- e negado por padrao: uma rota nova nasce
bloqueada para professor ate ser liberada aqui.
"""
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import Resolver404, resolve

from . import models

# Telas e APIs que o professor pode abrir sem checagem de dono (os dados ja sao filtrados nas views).
ROTAS_LIVRES = {
    "dashboard",  # a propria view manda o professor para a agenda
    "aulas_list",
    "aulas_semana",
    "aulas_operacao_api",
    "evolucao_enriquecer_api",
    "perfil",
    "password_change",
    "password_change_done",
    "login",
    "logout",
    # publicas por token (aluno assinando, webhook do TotalPass, app do aluno)
    "totalpass_webhook",
    "contrato_assinar",
    "contrato_pdf",
    "termo_assinar",
    "aluno_app",
    "aluno_app_manifest",
    "aluno_app_sw",
    "aluno_app_icon",
}

# rota -> nome do parametro da URL; a reserva precisa ser de uma aula do professor.
POR_RESERVA = {
    "aulas_evolucao_api": "reserva_id",
    "aulas_evolucao_enriquecer_api": "reserva_id",
    "aulas_avaliacoes_api": "reserva_id",
    "aulas_historico_api": "reserva_id",
    "aulas_status_api": "reserva_id",
    "aulas_whatsapp_now_api": "reserva_id",
    "reservas_evoluir": "pk",
}

# rota -> parametro; o aluno precisa ter ao menos uma reserva em aula do professor.
POR_ALUNO = {
    "alunos_detail": "pk",
    "alunos_evolucao_create": "aluno_id",
    "alunos_avaliacao_create": "aluno_id",
    "evolucoes_exportar_pdf": "aluno_id",
    "evolucoes_exportar_excel": "aluno_id",
}

POR_EVOLUCAO = {"alunos_evolucao_update": "evolucao_id", "alunos_evolucao_delete": "evolucao_id"}
POR_AVALIACAO = {"alunos_avaliacao_update": "avaliacao_id", "alunos_avaliacao_delete": "avaliacao_id"}


def reserva_e_do_professor(reserva_id, profissional):
    return models.Reserva.objects.filter(pk=reserva_id, aulaSessao__profissional=profissional).exists()


def aluno_e_do_professor(aluno_id, profissional):
    return models.Reserva.objects.filter(aluno_id=aluno_id, aulaSessao__profissional=profissional).exists()


def professor_pode_acessar(nome_rota, kwargs, profissional):
    """True se o professor pode abrir essa rota com esses parametros."""
    if nome_rota in ROTAS_LIVRES:
        return True
    if nome_rota in POR_RESERVA:
        return reserva_e_do_professor(kwargs.get(POR_RESERVA[nome_rota]), profissional)
    if nome_rota in POR_ALUNO:
        return aluno_e_do_professor(kwargs.get(POR_ALUNO[nome_rota]), profissional)
    if nome_rota in POR_EVOLUCAO:
        return models.EvolucaoAluno.objects.filter(
            pk=kwargs.get(POR_EVOLUCAO[nome_rota]), reserva__aulaSessao__profissional=profissional
        ).exists()
    if nome_rota in POR_AVALIACAO:
        return models.AvaliacaoAluno.objects.filter(
            pk=kwargs.get(POR_AVALIACAO[nome_rota]), reserva__aulaSessao__profissional=profissional
        ).exists()
    return False


class ProfessorAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated and not user.is_superuser:
            profissional = (
                models.Profissional.objects.select_related("cdPerfilAcesso").filter(user=user).first()
            )
            perfil = ((profissional.cdPerfilAcesso.dsPerfilAcesso if profissional and profissional.cdPerfilAcesso_id else "") or "")
            if profissional and "professor" in perfil.strip().lower():
                try:
                    match = resolve(request.path_info)
                except Resolver404:
                    return self.get_response(request)
                if not professor_pode_acessar(match.url_name, match.kwargs, profissional):
                    return self._negar(request, match.url_name)
        return self.get_response(request)

    @staticmethod
    def _negar(request, nome_rota):
        e_api = (
            (nome_rota or "").endswith("_api")
            or request.path_info.startswith("/agenda/aulas/reservas/")
            or request.headers.get("X-Requested-With") == "XMLHttpRequest"
        )
        if e_api:
            return JsonResponse({"error": "Sem permissao para acessar esta area."}, status=403)
        messages.error(request, "Sem permissao para acessar esta area.")
        return redirect("aulas_list")
