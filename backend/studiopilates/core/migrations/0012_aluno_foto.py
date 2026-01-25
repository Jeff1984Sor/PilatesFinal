from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0011_contrato_valores"),
    ]

    operations = [
        migrations.AddField(
            model_name="aluno",
            name="foto",
            field=models.ImageField(blank=True, null=True, upload_to="alunos"),
        ),
    ]
