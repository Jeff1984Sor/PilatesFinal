from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0035_contrato_modo_pagamento"),
    ]

    operations = [
        migrations.AddField(
            model_name="plano",
            name="subcategoria_receita",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to="core.subcategoria"),
        ),
    ]
