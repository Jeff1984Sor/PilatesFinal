from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0027_alter_contrato_status"),
    ]

    operations = [
        migrations.CreateModel(
            name="AlunoWhatsappMessage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("tipo", models.CharField(choices=[("manual", "Manual"), ("automated_reminder", "Lembrete diário"), ("professor_schedule", "Agenda do professor"), ("contract_link", "Link do contrato"), ("contract_renewal", "Renovação de contrato")], default="manual", max_length=30)),
                ("telefone", models.CharField(blank=True, max_length=20)),
                ("mensagem", models.TextField()),
                ("status", models.CharField(default="sent", max_length=20)),
                ("response_payload", models.TextField(blank=True)),
                ("enviado_em", models.DateTimeField(default=django.utils.timezone.now)),
                ("aluno", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="whatsapp_messages", to="core.aluno")),
                ("contrato", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="whatsapp_messages", to="core.contrato")),
            ],
            options={
                "ordering": ["-enviado_em"],
            },
        ),
    ]
