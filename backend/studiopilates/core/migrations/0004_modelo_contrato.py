from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0003_plano_duracao_aulas"),
    ]

    operations = [
        migrations.CreateModel(
            name="ModeloContrato",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("cdModeloContrato", models.IntegerField(db_index=True, unique=True)),
                ("dsNome", models.CharField(max_length=120)),
                ("conteudo_html", models.TextField()),
                ("ativo", models.BooleanField(default=True)),
                ("dtCadastro", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.AddField(
            model_name="plano",
            name="modeloContrato",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="core.modelocontrato"),
        ),
    ]
