from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0018_contas_pagar_recorrencia_quantidade"),
    ]

    operations = [
        migrations.AddField(
            model_name="contaspagar",
            name="status",
            field=models.CharField(choices=[("AGENDADO", "AGENDADO"), ("PAGO", "PAGO"), ("ATRASADO", "ATRASADO"), ("CANCELADO", "CANCELADO")], default="AGENDADO", max_length=10),
        ),
        migrations.AddField(
            model_name="contaspagar",
            name="dtPagamento",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="contaspagar",
            name="comprovante",
            field=models.FileField(blank=True, null=True, upload_to="comprovantes/contas_pagar"),
        ),
    ]
