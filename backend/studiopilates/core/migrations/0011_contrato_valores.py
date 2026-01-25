from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0010_plano_valor"),
    ]

    operations = [
        migrations.AddField(
            model_name="contrato",
            name="valor_parcela",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name="contrato",
            name="valor_total",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
    ]
