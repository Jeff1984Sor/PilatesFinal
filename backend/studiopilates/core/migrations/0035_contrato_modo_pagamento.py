from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0034_profissao_estado_civil"),
    ]

    operations = [
        migrations.AddField(
            model_name="contrato",
            name="modo_pagamento",
            field=models.CharField(
                blank=True,
                choices=[
                    ("DINHEIRO", "Dinheiro"),
                    ("PIX", "Pix"),
                    ("CREDITO", "Cartao de credito"),
                    ("DEBITO", "Cartao de debito"),
                ],
                max_length=20,
            ),
        ),
    ]
