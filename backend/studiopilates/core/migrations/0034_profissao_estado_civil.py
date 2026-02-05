from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0033_totalpass_configuracao"),
    ]

    operations = [
        migrations.CreateModel(
            name="Profissao",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("cdProfissao", models.IntegerField(db_index=True, unique=True)),
                ("dsProfissao", models.CharField(max_length=120)),
            ],
        ),
        migrations.AddField(
            model_name="aluno",
            name="estado_civil",
            field=models.CharField(
                blank=True,
                choices=[
                    ("SOLTEIRO", "Solteiro(a)"),
                    ("CASADO", "Casado(a)"),
                    ("DIVORCIADO", "Divorciado(a)"),
                    ("VIUVO", "Viuvo(a)"),
                    ("SEPARADO", "Separado(a)"),
                    ("UNIAO_ESTAVEL", "Uniao estavel"),
                    ("OUTRO", "Outro"),
                ],
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="aluno",
            name="cdProfissao",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="core.profissao"),
        ),
    ]
