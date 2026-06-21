# -*- coding: utf-8 -*-
"""Recalcula valor_aula, valor_parcela e valor_total dos contratos com a regra atual:
  - valor_parcela = valor mensal do plano
  - valor_total   = valor mensal x duracao_meses
  - valor_aula    = valor mensal / (aulas_por_semana x 4)

Uso:
    python manage.py recalcular_contratos            # dry-run (so mostra o que mudaria)
    python manage.py recalcular_contratos --apply    # grava as mudancas
    python manage.py recalcular_contratos --id 13    # so o contrato de id 13
    python manage.py recalcular_contratos --id 13 --apply
"""
from decimal import Decimal, ROUND_HALF_UP

from django.core.management.base import BaseCommand

from studiopilates.core import models


def _precos(plano):
    valor = Decimal(str(getattr(plano, "valor", 0) or 0))
    aulas_semana = int(getattr(plano, "aulas_por_semana", 0) or 0)
    duracao = int(getattr(plano, "duracao_meses", 0) or 0) or 1
    aulas_mes = aulas_semana * 4
    valor_aula = (valor / Decimal(aulas_mes)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if aulas_mes else None
    return valor_aula, valor, valor * duracao  # aula, parcela, total


class Command(BaseCommand):
    help = "Recalcula valores (aula/parcela/total) dos contratos com a regra atual."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true", help="Grava as mudancas (sem isso e dry-run)")
        parser.add_argument("--id", type=int, default=None, help="Recalcular apenas o contrato com esse id")

    def handle(self, *args, **options):
        apply = options.get("apply")
        contrato_id = options.get("id")

        qs = models.Contrato.objects.select_related("cdPlano")
        if contrato_id:
            qs = qs.filter(pk=contrato_id)

        mudados = 0
        for c in qs:
            plano = c.cdPlano
            if not plano:
                continue
            n_aula, n_parcela, n_total = _precos(plano)
            antigo = (c.valor_aula, c.valor_parcela, c.valor_total)
            novo = (n_aula, n_parcela, n_total)
            # compara como Decimal/None
            def _eq(a, b):
                if a is None or b is None:
                    return a == b
                return Decimal(str(a)) == Decimal(str(b))
            if all(_eq(antigo[i], novo[i]) for i in range(3)):
                continue
            mudados += 1
            self.stdout.write(
                f"Contrato #{c.cdContrato} ({plano.dsPlano}): "
                f"aula {antigo[0]}->{n_aula} | parcela {antigo[1]}->{n_parcela} | total {antigo[2]}->{n_total}"
            )
            if apply:
                c.valor_aula = n_aula
                c.valor_parcela = n_parcela
                c.valor_total = n_total
                c.save(update_fields=["valor_aula", "valor_parcela", "valor_total"])

        if not mudados:
            self.stdout.write(self.style.SUCCESS("Nenhum contrato precisa de ajuste."))
        elif apply:
            self.stdout.write(self.style.SUCCESS(f"{mudados} contrato(s) atualizados."))
        else:
            self.stdout.write(self.style.WARNING(f"{mudados} contrato(s) seriam alterados. Rode com --apply para gravar."))
