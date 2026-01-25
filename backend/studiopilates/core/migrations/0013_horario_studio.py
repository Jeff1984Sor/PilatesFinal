from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0012_aluno_foto"),
    ]

    operations = [
        migrations.CreateModel(
            name="HorarioStudio",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("cdHorario", models.IntegerField(db_index=True, unique=True)),
                (
                    "diaSemana",
                    models.IntegerField(
                        choices=[
                            (0, "Segunda"),
                            (1, "Terca"),
                            (2, "Quarta"),
                            (3, "Quinta"),
                            (4, "Sexta"),
                            (5, "Sabado"),
                            (6, "Domingo"),
                        ]
                    ),
                ),
                ("horaInicio", models.TimeField()),
                ("horaFim", models.TimeField()),
                ("capacidade", models.IntegerField(blank=True, null=True)),
                ("tipoServico", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="core.tiposervico")),
                ("unidade", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="core.unidade")),
            ],
        ),
    ]
