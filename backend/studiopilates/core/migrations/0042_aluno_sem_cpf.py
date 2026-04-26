from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0041_aluno_autoriza_imagem"),
    ]

    operations = [
        migrations.AlterField(
            model_name="aluno",
            name="dsCPF",
            field=models.CharField(blank=True, max_length=32, unique=True),
        ),
        migrations.AddField(
            model_name="aluno",
            name="sem_cpf",
            field=models.BooleanField(default=False),
        ),
    ]
