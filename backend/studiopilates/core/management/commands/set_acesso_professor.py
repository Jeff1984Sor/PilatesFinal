# -*- coding: utf-8 -*-
"""Da a profissionais o perfil "Professor": so a agenda e as proprias aulas, sem financeiro.

Uso:
    python manage.py set_acesso_professor Natalia Ranieli      # aplica
    python manage.py set_acesso_professor Natalia --simular    # so mostra o que faria

Cada nome precisa achar exatamente 1 profissional (busca por parte do nome).
O login (usuario) e o e-mail do profissional; a senha se define com:
    python manage.py changepassword <usuario>
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from studiopilates.core import models

NOME_PERFIL = "Professor"


class Command(BaseCommand):
    help = "Atribui o perfil Professor (acesso so as proprias aulas) a um ou mais profissionais."

    def add_arguments(self, parser):
        parser.add_argument("nomes", nargs="+", help="parte do nome de cada profissional")
        parser.add_argument("--simular", action="store_true", help="nao grava nada, so mostra")

    @transaction.atomic
    def handle(self, *args, **options):
        escolhidos = []
        for termo in options["nomes"]:
            achados = list(models.Profissional.objects.filter(profissional__icontains=termo).select_related("user"))
            if len(achados) != 1:
                nomes = ", ".join(p.profissional for p in achados) or "ninguem"
                raise CommandError(f'"{termo}" deve achar exatamente 1 profissional, achou {len(achados)}: {nomes}')
            prof = achados[0]
            if prof.user and prof.user.is_superuser:
                raise CommandError(f"{prof.profissional} e superusuario; nao vou limitar o acesso dele.")
            escolhidos.append(prof)

        perfil = models.PerfilAcesso.objects.filter(dsPerfilAcesso__iexact=NOME_PERFIL).first()
        if perfil is None:
            proximo = (models.PerfilAcesso.objects.order_by("-cdPerfilAcesso").values_list("cdPerfilAcesso", flat=True).first() or 0) + 1
            if options["simular"]:
                self.stdout.write(f'[simulacao] criaria o perfil "{NOME_PERFIL}" (codigo {proximo})')
            else:
                perfil = models.PerfilAcesso.objects.create(cdPerfilAcesso=proximo, dsPerfilAcesso=NOME_PERFIL)
                self.stdout.write(f'Perfil "{NOME_PERFIL}" criado (codigo {proximo}).')

        for prof in escolhidos:
            antes = prof.cdPerfilAcesso.dsPerfilAcesso if prof.cdPerfilAcesso_id else "(sem perfil)"
            usuario = prof.user.username if prof.user else None
            if options["simular"]:
                self.stdout.write(f"[simulacao] {prof.profissional}: {antes} -> {NOME_PERFIL} | login: {usuario or 'SEM USUARIO'}")
                continue
            prof.cdPerfilAcesso = perfil
            prof.save(update_fields=["cdPerfilAcesso"])
            prof.refresh_from_db()
            usuario = prof.user.username if prof.user else None
            self.stdout.write(self.style.SUCCESS(f"{prof.profissional}: {antes} -> {NOME_PERFIL} | login: {usuario or 'SEM USUARIO'}"))
            if not usuario:
                self.stdout.write(self.style.WARNING("  sem usuario: edite o profissional na tela para gerar o login."))
