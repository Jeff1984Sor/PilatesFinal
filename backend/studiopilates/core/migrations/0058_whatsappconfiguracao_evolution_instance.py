from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0057_whatsappconfiguracao_acompanhamento"),
    ]

    operations = [
        migrations.AddField(
            model_name="whatsappconfiguracao",
            name="evolution_instance",
            field=models.CharField(blank=True, max_length=150),
        ),
    ]
