from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0040_contrato_recorrencia"),
    ]

    operations = [
        migrations.AddField(
            model_name="aluno",
            name="autoriza_imagem",
            field=models.BooleanField(default=False),
        ),
    ]
