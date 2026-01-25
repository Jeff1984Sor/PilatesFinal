from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0008_termo_nome_remove_ativo"),
    ]

    operations = [
        migrations.AddField(
            model_name="unidade",
            name="duracao_aula_minutos",
            field=models.IntegerField(default=50),
        ),
    ]
