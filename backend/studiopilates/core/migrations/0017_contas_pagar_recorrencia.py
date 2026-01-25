from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0016_evolucao_modelos"),
    ]

    operations = [
        migrations.AddField(
            model_name="contaspagar",
            name="recorrencia",
            field=models.CharField(blank=True, choices=[("MENSAL", "MENSAL"), ("SEMANAL", "SEMANAL"), ("ANUAL", "ANUAL")], max_length=10),
        ),
    ]
