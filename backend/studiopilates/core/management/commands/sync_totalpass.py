from django.core.management.base import BaseCommand
from django.utils import timezone
from studiopilates.core import models, totalpass_service, views


class Command(BaseCommand):
    help = "Sincroniza agendamentos do TotalPass."

    def add_arguments(self, parser):
        parser.add_argument("--date", help="Data alvo YYYY-MM-DD (padrao hoje).")

    def handle(self, *args, **options):
        target = options.get("date")
        if target:
            date_from = target
            date_to = target
        else:
            today = timezone.localdate().isoformat()
            date_from = today
            date_to = today

        configs = models.TotalpassConfiguracao.objects.filter(ativo=True).select_related("unidade")
        if not configs.exists():
            self.stdout.write(self.style.WARNING("Nenhuma configuracao TotalPass ativa."))
            return

        total_ok = 0
        total_fail = 0
        for cfg in configs:
            if not cfg.partner_api_key or not cfg.place_api_key:
                self.stdout.write(self.style.WARNING(f"Config sem chaves: unidade {cfg.unidade}"))
                continue
            try:
                token = totalpass_service.authenticate(cfg.partner_api_key, cfg.place_api_key)
                slots = totalpass_service.fetch_slots(token, date_from, date_to, cfg.place_id or "")
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f"Falha API TotalPass ({cfg.unidade}): {exc}"))
                total_fail += 1
                continue
            for slot in slots:
                payload = views._build_totalpass_payload_from_slot(slot)
                _, err = views._process_totalpass_payload(payload, cfg)
                if err:
                    total_fail += 1
                else:
                    total_ok += 1

        self.stdout.write(self.style.SUCCESS(f"TotalPass sync concluido. OK={total_ok} FAIL={total_fail}"))
