from django.core.management.base import BaseCommand

from studiopilates.core import models

NOME_BASE = "Aula Avulsa Total Pass / WellHub"


class Command(BaseCommand):
    help = (
        "Cria um plano avulso 'Aula Avulsa Total Pass / WellHub' com valor R$ 0 "
        "para cada tipo de servico cadastrado. Pode rodar varias vezes: nao duplica."
    )

    def handle(self, *args, **options):
        tipos = models.TipoServico.objects.all().order_by("cdTipoServico")
        if not tipos:
            self.stdout.write(self.style.WARNING("Nenhum tipo de servico cadastrado."))
            return

        criados = 0
        for tipo in tipos:
            nome = f"{NOME_BASE} - {tipo.dsTipoServico}"
            if models.Plano.objects.filter(dsPlano=nome).exists():
                self.stdout.write(f"ja existe: {nome}")
                continue
            ultimo_cd = models.Plano.objects.order_by("-cdPlano").values_list("cdPlano", flat=True).first() or 0
            models.Plano.objects.create(
                cdPlano=ultimo_cd + 1,
                dsPlano=nome,
                cdTipoServico=tipo,
                valor=0,
                aulas_por_semana=1,
                duracao_meses=1,
                recorrencia="SEMANAL",
                is_avulso=True,
            )
            criados += 1
            self.stdout.write(self.style.SUCCESS(f"criado: {nome}"))

        self.stdout.write(self.style.SUCCESS(f"{criados} plano(s) criado(s)."))
