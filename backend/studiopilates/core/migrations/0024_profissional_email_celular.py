from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0023_merge_20260125_1310"),
    ]

    operations = [
        migrations.AddField(
            model_name="profissional",
            name="email",
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.AddField(
            model_name="profissional",
            name="celular",
            field=models.CharField(blank=True, max_length=20),
        ),
    ]
