from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0009_unidade_duracao_aula"),
    ]

    operations = [
        migrations.AddField(
            model_name="plano",
            name="valor",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
    ]
