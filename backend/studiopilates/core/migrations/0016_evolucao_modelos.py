from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0015_contasreceber_pagamento"),
    ]

    operations = [
        migrations.CreateModel(
            name="ModeloEvolucao",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("cdModeloEvolucao", models.IntegerField(db_index=True, unique=True)),
                ("titulo", models.CharField(max_length=120)),
                ("texto", models.TextField()),
                ("ativo", models.BooleanField(default=True)),
                ("dtCadastro", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="EvolucaoAluno",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("texto", models.TextField()),
                ("dtEvolucao", models.DateTimeField(auto_now_add=True)),
                ("profissional", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="core.profissional")),
                ("reserva", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="evolucoes", to="core.reserva")),
            ],
        ),
    ]
