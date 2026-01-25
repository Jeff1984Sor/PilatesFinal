from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0014_horario_studio_profissional"),
    ]

    operations = [
        migrations.AddField(
            model_name="contasreceber",
            name="dtPagamento",
            field=models.DateField(blank=True, null=True),
        ),
    ]
