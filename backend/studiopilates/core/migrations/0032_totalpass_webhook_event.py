from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0031_avaliacao_aluno"),
    ]

    operations = [
        migrations.CreateModel(
            name="TotalpassWebhookEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("event_id", models.CharField(blank=True, max_length=100)),
                ("slot_id", models.CharField(blank=True, max_length=100)),
                ("user_document", models.CharField(blank=True, max_length=20)),
                ("status", models.CharField(blank=True, max_length=30)),
                ("payload", models.JSONField()),
                ("received_at", models.DateTimeField(auto_now_add=True)),
                ("processed_at", models.DateTimeField(blank=True, null=True)),
                ("error", models.TextField(blank=True)),
            ],
            options={
                "ordering": ["-received_at"],
            },
        ),
    ]

