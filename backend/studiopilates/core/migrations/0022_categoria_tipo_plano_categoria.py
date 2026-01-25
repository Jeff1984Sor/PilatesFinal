from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0021_conta_bancaria"),
    ]

    operations = [
        migrations.AddField(
            model_name="categoria",
            name="tipo",
            field=models.CharField(choices=[("RECEITA", "RECEITA"), ("DESPESA", "DESPESA")], default="DESPESA", max_length=10),
        ),
        migrations.AddField(
            model_name="plano",
            name="categoria_receita",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to="core.categoria"),
        ),
    ]
