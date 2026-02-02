from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0029_whatsappconfiguracao"),
    ]

    operations = [
        migrations.CreateModel(
            name="HorarioFuncionamento",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("diaSemana", models.IntegerField(choices=[(0, "Segunda"), (1, "Terca"), (2, "Quarta"), (3, "Quinta"), (4, "Sexta"), (5, "Sabado"), (6, "Domingo")])),
                ("horaInicio", models.TimeField()),
                ("horaFim", models.TimeField()),
                ("ativo", models.BooleanField(default=True)),
                ("tipoServico", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to="core.tiposervico")),
                ("unidade", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="core.unidade")),
            ],
            options={
                "ordering": ["unidade", "diaSemana", "horaInicio"],
                "unique_together": {("unidade", "tipoServico", "diaSemana", "horaInicio", "horaFim")},
            },
        ),
        migrations.CreateModel(
            name="BloqueioAgenda",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("recorrente", models.BooleanField(default=False)),
                ("diaSemana", models.IntegerField(blank=True, choices=[(0, "Segunda"), (1, "Terca"), (2, "Quarta"), (3, "Quinta"), (4, "Sexta"), (5, "Sabado"), (6, "Domingo")], null=True)),
                ("dataInicio", models.DateField()),
                ("dataFim", models.DateField(blank=True, null=True)),
                ("horaInicio", models.TimeField()),
                ("horaFim", models.TimeField()),
                ("motivo", models.CharField(blank=True, max_length=200)),
                ("ativo", models.BooleanField(default=True)),
                ("profissional", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to="core.profissional")),
                ("tipoServico", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to="core.tiposervico")),
                ("unidade", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="core.unidade")),
            ],
            options={
                "ordering": ["-dataInicio", "horaInicio"],
            },
        ),
    ]
