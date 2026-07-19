from django.core.management.base import BaseCommand

from studiopilates.core import services


class Command(BaseCommand):
    help = (
        "Marca como CONCLUIDA (realizada) toda aula sem tratativa cujo horario ja "
        "passou. Nao altera aulas canceladas, faltas ou ja concluidas."
    )

    def handle(self, *args, **options):
        total = services.concluir_aulas_passadas()
        self.stdout.write(self.style.SUCCESS(f"{total} aula(s) marcada(s) como realizada."))
