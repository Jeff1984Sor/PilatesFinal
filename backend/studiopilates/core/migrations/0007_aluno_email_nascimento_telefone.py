from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0006_remove_tipoplano_recorrencia"),
    ]

    operations = [
        migrations.AddField(
            model_name="aluno",
            name="dsEmail",
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.AddField(
            model_name="aluno",
            name="dtNascimento",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name="TelefoneAluno",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("cdTelefone", models.IntegerField(db_index=True, unique=True)),
                ("dsTelefone", models.CharField(max_length=20)),
                ("dtCadastro", models.DateTimeField(auto_now_add=True)),
                ("cdAluno", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="telefones", to="core.aluno")),
            ],
        ),
    ]
