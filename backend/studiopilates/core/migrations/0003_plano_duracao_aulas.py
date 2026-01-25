from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0002_profissional_user"),
    ]

    operations = [
        migrations.AddField(
            model_name="tipoplano",
            name="duracao",
            field=models.CharField(
                choices=[("MENSAL", "Mensal"), ("TRIMESTRAL", "Trimestral"), ("SEMESTRAL", "Semestral"), ("ANUAL", "Anual")],
                default="MENSAL",
                max_length=12,
            ),
        ),
        migrations.AddField(
            model_name="plano",
            name="aulas_por_semana",
            field=models.IntegerField(default=1),
        ),
    ]
