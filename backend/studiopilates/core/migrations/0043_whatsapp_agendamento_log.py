from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0042_aluno_sem_cpf"),
    ]

    operations = [
        migrations.CreateModel(
            name="WhatsappAgendamentoLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("tipo", models.CharField(choices=[("manual", "Manual"), ("automated_reminder", "Lembrete diário"), ("professor_schedule", "Agenda do professor"), ("contract_link", "Link do contrato"), ("contract_pdf", "Contrato em PDF"), ("contract_renewal", "Renovação de contrato")], max_length=30)),
                ("dedupe_key", models.CharField(max_length=220, unique=True)),
                ("data_referencia", models.DateField()),
                ("telefone", models.CharField(blank=True, max_length=20)),
                ("mensagem", models.TextField()),
                ("status", models.CharField(default="sent", max_length=20)),
                ("response_payload", models.TextField(blank=True)),
                ("enviado_em", models.DateTimeField(default=django.utils.timezone.now)),
                ("aluno", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="whatsapp_agendamentos", to="core.aluno")),
                ("contrato", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="whatsapp_agendamentos", to="core.contrato")),
                ("profissional", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="whatsapp_agendamentos", to="core.profissional")),
                ("unidade", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="whatsapp_agendamentos", to="core.unidade")),
            ],
            options={
                "ordering": ["-enviado_em"],
            },
        ),
    ]
