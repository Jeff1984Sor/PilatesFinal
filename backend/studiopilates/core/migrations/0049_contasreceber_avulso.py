from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0048_horariofuncionamento_multiservico"),
    ]

    operations = [
        migrations.AddField(
            model_name="contasreceber",
            name="aluno",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="contas_avulsas",
                to="core.aluno",
            ),
        ),
        migrations.AddField(
            model_name="contasreceber",
            name="descricao",
            field=models.CharField(blank=True, default="", max_length=200),
            preserve_default=False,
        ),
    ]
