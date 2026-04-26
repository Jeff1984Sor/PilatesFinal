from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0038_alter_alunowhatsappmessage_tipo_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="plano",
            name="recorrencia",
            field=models.CharField(
                choices=[("SEMANAL", "Semanal"), ("MENSAL", "Mensal")],
                default="MENSAL",
                max_length=10,
            ),
        ),
    ]
