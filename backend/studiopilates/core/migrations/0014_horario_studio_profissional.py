from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0013_horario_studio"),
    ]

    operations = [
        migrations.AddField(
            model_name="horariostudio",
            name="profissional",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to="core.profissional"),
        ),
    ]
