from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0007_aluno_email_nascimento_telefone"),
    ]

    operations = [
        migrations.AddField(
            model_name="termouso",
            name="nome",
            field=models.CharField(default="Termo", max_length=80),
            preserve_default=False,
        ),
        migrations.RemoveField(
            model_name="termouso",
            name="versao",
        ),
        migrations.RemoveField(
            model_name="termouso",
            name="ativo",
        ),
    ]
