from django.db import migrations, models


def copy_primary_service_to_multiservico(apps, schema_editor):
    HorarioFuncionamento = apps.get_model("core", "HorarioFuncionamento")
    for horario in HorarioFuncionamento.objects.exclude(tipoServico__isnull=True):
        horario.tipos_servico.add(horario.tipoServico_id)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0047_aula_avulsa_and_receber_links"),
    ]

    operations = [
        migrations.AddField(
            model_name="horariofuncionamento",
            name="tipos_servico",
            field=models.ManyToManyField(blank=True, related_name="horarios_funcionamento", to="core.tiposervico"),
        ),
        migrations.RunPython(copy_primary_service_to_multiservico, noop_reverse),
    ]
