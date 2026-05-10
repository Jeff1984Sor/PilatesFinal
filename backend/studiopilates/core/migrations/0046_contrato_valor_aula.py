from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0045_alunodocumento"),
    ]

    operations = [
        migrations.AddField(
            model_name="contrato",
            name="valor_aula",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
    ]
