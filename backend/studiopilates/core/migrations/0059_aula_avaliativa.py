import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0058_whatsappconfiguracao_evolution_instance"),
    ]

    operations = [
        migrations.CreateModel(
            name="AulaAvaliativa",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("cdAulaAvaliativa", models.IntegerField(db_index=True, unique=True)),
                ("data", models.DateField()),
                ("horaInicio", models.TimeField()),
                ("horaFim", models.TimeField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("AGENDADA", "Agendada"),
                            ("REALIZADA", "Realizada"),
                            ("CANCELADA", "Cancelada"),
                            ("CONVERTIDA", "Convertida em contrato"),
                        ],
                        default="AGENDADA",
                        max_length=20,
                    ),
                ),
                ("queixa_principal", models.TextField(blank=True)),
                ("objetivos", models.TextField(blank=True)),
                ("historico_saude", models.TextField(blank=True)),
                ("observacoes", models.TextField(blank=True)),
                ("dtCadastro", models.DateTimeField(auto_now_add=True)),
                (
                    "aluno",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="aulas_avaliativas",
                        to="core.aluno",
                    ),
                ),
                (
                    "contrato",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="aulas_avaliativas",
                        to="core.contrato",
                    ),
                ),
                (
                    "profissional",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="core.profissional"),
                ),
                (
                    "tipoServico",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to="core.tiposervico",
                    ),
                ),
                (
                    "unidade",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="core.unidade"),
                ),
            ],
            options={
                "ordering": ["-data", "-horaInicio"],
            },
        ),
        migrations.AddField(
            model_name="reserva",
            name="aula_avaliativa",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="reservas",
                to="core.aulaavaliativa",
            ),
        ),
    ]
