from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0043_whatsapp_agendamento_log"),
    ]

    operations = [
        migrations.AddField(
            model_name="aluno",
            name="status",
            field=models.CharField(choices=[("ATIVO", "Ativo"), ("INATIVO", "Inativo")], db_index=True, default="ATIVO", max_length=10),
        ),
    ]
