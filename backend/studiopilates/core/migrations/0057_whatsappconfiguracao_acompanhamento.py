from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0056_contasreceber_aluno_contasreceber_descricao"),
    ]

    operations = [
        migrations.AddField(
            model_name="whatsappconfiguracao",
            name="acompanhar_envios",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="whatsappconfiguracao",
            name="numero_acompanhamento",
            field=models.CharField(blank=True, max_length=20),
        ),
    ]
