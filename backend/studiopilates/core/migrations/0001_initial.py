from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="PerfilAcesso",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("cdPerfilAcesso", models.IntegerField(db_index=True, unique=True)),
                ("dsPerfilAcesso", models.CharField(max_length=120)),
            ],
        ),
        migrations.CreateModel(
            name="Recorrencia",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("cdRecorrencia", models.IntegerField(db_index=True, unique=True)),
                ("dsRecorrencia", models.CharField(max_length=80)),
            ],
        ),
        migrations.CreateModel(
            name="TipoServico",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("cdTipoServico", models.IntegerField(db_index=True, unique=True)),
                ("dsTipoServico", models.CharField(max_length=80)),
            ],
        ),
        migrations.CreateModel(
            name="Unidade",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("cdUnidade", models.IntegerField(db_index=True, unique=True)),
                ("dsUnidade", models.CharField(max_length=120)),
                ("capacidade", models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name="TermoUso",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("cdTermoUso", models.IntegerField(db_index=True, unique=True)),
                ("dsTermoUso", models.TextField()),
                ("versao", models.CharField(blank=True, max_length=20)),
                ("ativo", models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name="TipoPlano",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("cdTipoPlano", models.IntegerField(db_index=True, unique=True)),
                ("dsTipoPlano", models.CharField(max_length=80)),
                ("cdRecorrencia", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="core.recorrencia")),
            ],
        ),
        migrations.CreateModel(
            name="Plano",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("cdPlano", models.IntegerField(db_index=True, unique=True)),
                ("dsPlano", models.CharField(max_length=120)),
                ("cdTipoPlano", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="core.tipoplano")),
                ("cdTipoServico", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="core.tiposervico")),
            ],
        ),
        migrations.CreateModel(
            name="Fornecedor",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("cdFornecedor", models.IntegerField(db_index=True, unique=True)),
                ("dsFornecedor", models.CharField(max_length=120)),
            ],
        ),
        migrations.CreateModel(
            name="Categoria",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("cdCategoria", models.IntegerField(db_index=True, unique=True)),
                ("dsCategoria", models.CharField(max_length=120)),
            ],
        ),
        migrations.CreateModel(
            name="Subcategoria",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("cdSubcategoria", models.IntegerField(db_index=True, unique=True)),
                ("dsSubcategoria", models.CharField(max_length=120)),
                ("cdCategoria", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="core.categoria")),
            ],
        ),
        migrations.CreateModel(
            name="Profissional",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("cdProfissional", models.IntegerField(db_index=True, unique=True)),
                ("profissional", models.CharField(max_length=150)),
                ("dtNascimento", models.DateField(blank=True, null=True)),
                ("crefito", models.CharField(blank=True, max_length=50)),
                ("dtCadastro", models.DateTimeField(auto_now_add=True)),
                ("cdPerfilAcesso", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="core.perfilacesso")),
            ],
        ),
        migrations.CreateModel(
            name="Aluno",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("cdAluno", models.IntegerField(db_index=True, unique=True)),
                ("dsNome", models.CharField(max_length=150)),
                ("dsCPF", models.CharField(max_length=14, unique=True)),
                ("dsRg", models.CharField(blank=True, max_length=30)),
                ("dtCadastro", models.DateTimeField(auto_now_add=True)),
                ("termo_aceite_em", models.DateTimeField(blank=True, null=True)),
                ("cdTermoUso", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="core.termouso")),
                ("cdUnidade", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="core.unidade")),
            ],
        ),
        migrations.CreateModel(
            name="EnderecoAluno",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("cdEndereco", models.IntegerField(db_index=True, unique=True)),
                ("dsLogradouro", models.CharField(max_length=150)),
                ("dsNumero", models.CharField(max_length=20)),
                ("dsCEP", models.CharField(max_length=12)),
                ("dsCidade", models.CharField(max_length=80)),
                ("dsBairro", models.CharField(max_length=80)),
                ("dtCadastro", models.DateTimeField(auto_now_add=True)),
                ("cdAluno", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="endereco", to="core.aluno")),
            ],
        ),
        migrations.AddField(
            model_name="aluno",
            name="cdEndereco",
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="core.enderecoaluno"),
        ),
        migrations.CreateModel(
            name="Contrato",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("cdContrato", models.IntegerField(db_index=True, unique=True)),
                ("dtCadastro", models.DateTimeField(auto_now_add=True)),
                ("dtInicioContrato", models.DateField()),
                ("dtFimContrato", models.DateField()),
                ("cdAluno", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="core.aluno")),
                ("cdPlano", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="core.plano")),
                ("cdProfissional", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="core.profissional")),
                ("cdTipoPlano", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="core.tipoplano")),
                ("cdUnidade", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="core.unidade")),
            ],
        ),
        migrations.CreateModel(
            name="ContasPagar",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("cdContasPagar", models.IntegerField(db_index=True, unique=True)),
                ("dtVencimento", models.DateField()),
                ("dtCadastro", models.DateTimeField(auto_now_add=True)),
                ("valor", models.DecimalField(decimal_places=2, max_digits=10)),
                ("cdCategoria", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="core.categoria")),
                ("cdFornecedor", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="core.fornecedor")),
                ("cdSubcategoria", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="core.subcategoria")),
            ],
        ),
        migrations.CreateModel(
            name="AulaSessao",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("data", models.DateField()),
                ("horaInicio", models.TimeField()),
                ("horaFim", models.TimeField()),
                ("capacidade", models.IntegerField(blank=True, null=True)),
                ("dtCadastro", models.DateTimeField(auto_now_add=True)),
                ("profissional", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="core.profissional")),
                ("tipoServico", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="core.tiposervico")),
                ("unidade", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="core.unidade")),
            ],
        ),
        migrations.CreateModel(
            name="Reserva",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("RESERVADA", "RESERVADA"), ("CANCELADA", "CANCELADA"), ("CONCLUIDA", "CONCLUIDA"), ("PENDENTE", "PENDENTE")], default="RESERVADA", max_length=20)),
                ("dtCadastro", models.DateTimeField(auto_now_add=True)),
                ("aluno", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="core.aluno")),
                ("aulaSessao", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="core.aulasessao")),
            ],
            options={"unique_together": {("aluno", "aulaSessao")}},
        ),
        migrations.CreateModel(
            name="ContasReceber",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("ABERTO", "ABERTO"), ("PAGO", "PAGO"), ("ATRASADO", "ATRASADO"), ("CANCELADO", "CANCELADO")], default="ABERTO", max_length=20)),
                ("valor", models.DecimalField(decimal_places=2, max_digits=10)),
                ("dtVencimento", models.DateField()),
                ("competencia", models.CharField(blank=True, max_length=7)),
                ("dtCadastro", models.DateTimeField(auto_now_add=True)),
                ("contrato", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="core.contrato")),
            ],
        ),
    ]
