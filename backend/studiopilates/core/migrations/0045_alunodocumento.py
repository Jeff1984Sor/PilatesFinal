from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0044_aluno_status"),
    ]

    operations = [
        migrations.CreateModel(
            name="AlunoDocumento",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("cdDocumento", models.IntegerField(db_index=True, unique=True)),
                ("titulo", models.CharField(max_length=150)),
                ("arquivo", models.FileField(upload_to="alunos/documentos")),
                ("descricao", models.TextField(blank=True)),
                ("origem", models.CharField(choices=[("UPLOAD", "Enviado manualmente"), ("CONTRATO_PDF", "Gerado pelo sistema")], default="UPLOAD", max_length=20)),
                ("dtCadastro", models.DateTimeField(auto_now_add=True)),
                ("aluno", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="documentos", to="core.aluno")),
                ("contrato", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="documentos", to="core.contrato")),
            ],
            options={
                "ordering": ["-dtCadastro"],
            },
        ),
    ]
