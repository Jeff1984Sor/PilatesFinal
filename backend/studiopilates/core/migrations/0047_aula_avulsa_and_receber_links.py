from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0046_contrato_valor_aula"),
    ]

    operations = [
        migrations.CreateModel(
            name="AulaAvulsa",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("cdAulaAvulsa", models.IntegerField(db_index=True, unique=True)),
                (
                    "recorrencia",
                    models.CharField(
                        choices=[("SEMANAL", "Semanal"), ("MENSAL", "Mensal")],
                        default="SEMANAL",
                        max_length=10,
                    ),
                ),
                ("quantidade", models.IntegerField(default=1)),
                ("valor_aula", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("valor_total", models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ("dtInicio", models.DateField()),
                ("dtFim", models.DateField()),
                ("dtCadastro", models.DateTimeField(auto_now_add=True)),
                ("aluno", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="aulas_avulsas", to="core.aluno")),
                ("plano", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="core.plano")),
                ("profissional", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="core.profissional")),
                ("unidade", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="core.unidade")),
            ],
        ),
        migrations.AddField(
            model_name="reserva",
            name="pacote_avulso",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="reservas",
                to="core.aulaavulsa",
            ),
        ),
        migrations.AlterField(
            model_name="contasreceber",
            name="contrato",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to="core.contrato"),
        ),
        migrations.AddField(
            model_name="contasreceber",
            name="reserva",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="contas_receber",
                to="core.reserva",
            ),
        ),
    ]
