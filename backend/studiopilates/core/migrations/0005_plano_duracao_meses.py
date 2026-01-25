from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0004_modelo_contrato"),
    ]

    operations = [
        migrations.AddField(
            model_name="plano",
            name="duracao_meses",
            field=models.IntegerField(default=1),
        ),
    ]
