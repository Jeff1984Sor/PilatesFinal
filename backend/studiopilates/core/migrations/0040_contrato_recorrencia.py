from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0039_plano_recorrencia"),
    ]

    operations = [
        migrations.AddField(
            model_name="contrato",
            name="recorrencia",
            field=models.CharField(
                choices=[("SEMANAL", "Semanal"), ("MENSAL", "Mensal")],
                default="MENSAL",
                max_length=10,
            ),
        ),
    ]
