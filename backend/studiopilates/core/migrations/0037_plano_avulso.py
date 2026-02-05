from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0036_plano_subcategoria_receita"),
    ]

    operations = [
        migrations.AddField(
            model_name="plano",
            name="is_avulso",
            field=models.BooleanField(default=False),
        ),
    ]
