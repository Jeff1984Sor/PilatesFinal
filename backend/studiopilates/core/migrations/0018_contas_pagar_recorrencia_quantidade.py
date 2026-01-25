from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0017_contas_pagar_recorrencia"),
    ]

    operations = [
        migrations.AddField(
            model_name="contaspagar",
            name="recorrencia_quantidade",
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
