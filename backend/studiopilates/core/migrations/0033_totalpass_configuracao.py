from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0032_totalpass_webhook_event"),
    ]

    operations = [
        migrations.CreateModel(
            name="TotalpassConfiguracao",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("ativo", models.BooleanField(default=True)),
                ("partner_api_key", models.CharField(blank=True, max_length=200)),
                ("place_api_key", models.CharField(blank=True, max_length=200)),
                ("place_id", models.CharField(blank=True, max_length=120)),
                ("webhook_token", models.CharField(blank=True, max_length=200)),
                ("criar_aluno_automatico", models.BooleanField(default=True)),
                ("somente_dia", models.BooleanField(default=True)),
                ("dtCadastro", models.DateTimeField(auto_now_add=True)),
                ("unidade", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="totalpass_configuracao", to="core.unidade")),
            ],
            options={
                "verbose_name": "Configuracao TotalPass",
                "verbose_name_plural": "Configuracoes TotalPass",
            },
        ),
    ]

