from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0030_horario_funcionamento_bloqueio"),
    ]

    operations = [
        migrations.CreateModel(
            name="AvaliacaoAluno",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("texto", models.TextField()),
                ("dtAvaliacao", models.DateTimeField(auto_now_add=True)),
                (
                    "profissional",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="core.profissional"),
                ),
                (
                    "reserva",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name="avaliacoes", to="core.reserva"
                    ),
                ),
            ],
            options={"ordering": ["-dtAvaliacao"]},
        ),
    ]
