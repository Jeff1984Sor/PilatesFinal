from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0005_plano_duracao_meses"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="plano",
            name="cdTipoPlano",
        ),
        migrations.RemoveField(
            model_name="contrato",
            name="cdTipoPlano",
        ),
        migrations.DeleteModel(
            name="TipoPlano",
        ),
        migrations.DeleteModel(
            name="Recorrencia",
        ),
    ]
