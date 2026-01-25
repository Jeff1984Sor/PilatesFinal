from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0019_contas_pagar_status_pagamento"),
    ]

    operations = [
        migrations.AddField(
            model_name="contaspagar",
            name="motivo_cancelamento",
            field=models.TextField(blank=True),
        ),
    ]
