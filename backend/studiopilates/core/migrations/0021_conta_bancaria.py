from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0020_contas_pagar_cancelamento"),
    ]

    operations = [
        migrations.CreateModel(
            name="ContaBancaria",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("cdConta", models.IntegerField(db_index=True, unique=True)),
                ("banco", models.CharField(max_length=120)),
                ("agencia", models.CharField(max_length=20)),
                ("conta", models.CharField(max_length=20)),
                ("saldo_inicial", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("ativo", models.BooleanField(default=True)),
                ("dtCadastro", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="MovimentoConta",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("tipo", models.CharField(choices=[("ENTRADA", "ENTRADA"), ("SAIDA", "SAIDA")], max_length=10)),
                ("valor", models.DecimalField(decimal_places=2, max_digits=12)),
                ("data", models.DateField()),
                ("descricao", models.CharField(blank=True, max_length=200)),
                ("comprovante", models.FileField(blank=True, null=True, upload_to="comprovantes/movimentos")),
                ("dtCadastro", models.DateTimeField(auto_now_add=True)),
                ("conta", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="movimentos", to="core.contabancaria")),
            ],
        ),
    ]
