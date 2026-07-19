from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0059_aula_avaliativa"),
    ]

    operations = [
        migrations.AddField(
            model_name="aulaavaliativa",
            name="tipo",
            field=models.CharField(
                choices=[
                    ("AVALIATIVA", "Aula Avaliativa"),
                    ("TOTALPASS", "Aula Avulsa Total Pass"),
                    ("WELLHUB", "Aula Avulsa WellHub"),
                ],
                default="AVALIATIVA",
                max_length=20,
            ),
        ),
    ]
