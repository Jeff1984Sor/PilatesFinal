from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from .validators import validar_cpf


class PerfilAcesso(models.Model):
    cdPerfilAcesso = models.IntegerField(unique=True, db_index=True)
    dsPerfilAcesso = models.CharField(max_length=120)

    def __str__(self):
        return self.dsPerfilAcesso


class Profissional(models.Model):
    cdProfissional = models.IntegerField(unique=True, db_index=True)
    profissional = models.CharField(max_length=150)
    email = models.EmailField(blank=True)
    celular = models.CharField(max_length=20, blank=True)
    cdPerfilAcesso = models.ForeignKey(PerfilAcesso, on_delete=models.PROTECT)
    dtNascimento = models.DateField(null=True, blank=True)
    crefito = models.CharField(max_length=50, blank=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    dtCadastro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.profissional


class Unidade(models.Model):
    cdUnidade = models.IntegerField(unique=True, db_index=True)
    dsUnidade = models.CharField(max_length=120)
    capacidade = models.IntegerField(default=0)
    duracao_aula_minutos = models.IntegerField(default=50)

    def __str__(self):
        return self.dsUnidade


class TermoUso(models.Model):
    cdTermoUso = models.IntegerField(unique=True, db_index=True)
    dsTermoUso = models.TextField()
    nome = models.CharField(max_length=80)

    def __str__(self):
        return self.nome


class Aluno(models.Model):
    cdAluno = models.IntegerField(unique=True, db_index=True)
    dsNome = models.CharField(max_length=150)
    dsCPF = models.CharField(max_length=14, unique=True)
    dsRg = models.CharField(max_length=30, blank=True)
    dsEmail = models.EmailField(blank=True)
    foto = models.ImageField(upload_to="alunos", null=True, blank=True)
    dtNascimento = models.DateField(null=True, blank=True)
    cdEndereco = models.OneToOneField("EnderecoAluno", on_delete=models.SET_NULL, null=True, blank=True)
    cdUnidade = models.ForeignKey(Unidade, on_delete=models.PROTECT)
    cdTermoUso = models.ForeignKey(TermoUso, on_delete=models.SET_NULL, null=True, blank=True)
    dtCadastro = models.DateTimeField(auto_now_add=True)
    termo_aceite_em = models.DateTimeField(null=True, blank=True)

    def clean(self):
        if not validar_cpf(self.dsCPF):
            raise ValidationError({"dsCPF": "CPF invalido"})

    def __str__(self):
        return self.dsNome


class EnderecoAluno(models.Model):
    cdEndereco = models.IntegerField(unique=True, db_index=True)
    cdAluno = models.OneToOneField(Aluno, on_delete=models.CASCADE, related_name="endereco")
    dsLogradouro = models.CharField(max_length=150)
    dsNumero = models.CharField(max_length=20)
    dsCEP = models.CharField(max_length=12)
    dsCidade = models.CharField(max_length=80)
    dsBairro = models.CharField(max_length=80)
    dtCadastro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.dsLogradouro}, {self.dsNumero}"


class TelefoneAluno(models.Model):
    cdTelefone = models.IntegerField(unique=True, db_index=True)
    cdAluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name="telefones")
    dsTelefone = models.CharField(max_length=20)
    dtCadastro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.dsTelefone


class WhatsappMessageType(models.TextChoices):
    MANUAL = "manual", "Manual"
    AUTOMATED_REMINDER = "automated_reminder", "Lembrete diário"
    PROFESSOR_SCHEDULE = "professor_schedule", "Agenda do professor"
    CONTRACT_LINK = "contract_link", "Link do contrato"
    CONTRACT_RENEWAL = "contract_renewal", "Renovação de contrato"


class AlunoWhatsappMessage(models.Model):
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name="whatsapp_messages")
    contrato = models.ForeignKey("Contrato", null=True, blank=True, on_delete=models.SET_NULL, related_name="whatsapp_messages")
    tipo = models.CharField(max_length=30, choices=WhatsappMessageType.choices, default=WhatsappMessageType.MANUAL)
    telefone = models.CharField(max_length=20, blank=True)
    mensagem = models.TextField()
    status = models.CharField(max_length=20, default="sent")
    response_payload = models.TextField(blank=True)
    enviado_em = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-enviado_em"]


class TipoServico(models.Model):
    cdTipoServico = models.IntegerField(unique=True, db_index=True)
    dsTipoServico = models.CharField(max_length=80)

    def __str__(self):
        return self.dsTipoServico


class HorarioStudio(models.Model):
    DIAS_SEMANA = [
        (0, "Segunda"),
        (1, "Terca"),
        (2, "Quarta"),
        (3, "Quinta"),
        (4, "Sexta"),
        (5, "Sabado"),
        (6, "Domingo"),
    ]

    cdHorario = models.IntegerField(unique=True, db_index=True)
    unidade = models.ForeignKey(Unidade, on_delete=models.PROTECT)
    tipoServico = models.ForeignKey(TipoServico, on_delete=models.PROTECT)
    profissional = models.ForeignKey(Profissional, on_delete=models.PROTECT, null=True, blank=True)
    diaSemana = models.IntegerField(choices=DIAS_SEMANA)
    horaInicio = models.TimeField()
    horaFim = models.TimeField()
    capacidade = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.get_diaSemana_display()} {self.horaInicio} - {self.horaFim}"


class Plano(models.Model):
    cdPlano = models.IntegerField(unique=True, db_index=True)
    dsPlano = models.CharField(max_length=120)
    cdTipoServico = models.ForeignKey(TipoServico, on_delete=models.PROTECT)
    categoria_receita = models.ForeignKey("Categoria", on_delete=models.PROTECT, null=True, blank=True)
    valor = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    aulas_por_semana = models.IntegerField(default=1)
    duracao_meses = models.IntegerField(default=1)
    modeloContrato = models.ForeignKey("ModeloContrato", on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.dsPlano


class Contrato(models.Model):
    STATUS_CHOICES = [
        ("NAO_ASSINADO", "Nao assinado"),
        ("ASSINADO", "Contrato assinado"),
        ("ASSINADO_DIGITALMENTE", "Assinado digitalmente"),
    ]

    cdContrato = models.IntegerField(unique=True, db_index=True)
    cdAluno = models.ForeignKey(Aluno, on_delete=models.PROTECT)
    cdPlano = models.ForeignKey(Plano, on_delete=models.PROTECT)
    cdUnidade = models.ForeignKey(Unidade, on_delete=models.PROTECT)
    cdProfissional = models.ForeignKey(Profissional, on_delete=models.PROTECT)
    valor_parcela = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    dtCadastro = models.DateTimeField(auto_now_add=True)
    dtInicioContrato = models.DateField()
    dtFimContrato = models.DateField()
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="NAO_ASSINADO")
    assinado_em = models.DateTimeField(null=True, blank=True)
    assinatura_nome = models.CharField(max_length=150, blank=True)
    assinatura_documento = models.CharField(max_length=30, blank=True)
    assinatura_ip = models.GenericIPAddressField(null=True, blank=True)
    assinatura_imagem = models.ImageField(upload_to="assinaturas", null=True, blank=True)

    def __str__(self):
        return f"Contrato {self.cdContrato}"


class Fornecedor(models.Model):
    cdFornecedor = models.IntegerField(unique=True, db_index=True)
    dsFornecedor = models.CharField(max_length=120)

    def __str__(self):
        return self.dsFornecedor


class Categoria(models.Model):
    TIPO_CHOICES = [
        ("RECEITA", "RECEITA"),
        ("DESPESA", "DESPESA"),
    ]

    cdCategoria = models.IntegerField(unique=True, db_index=True)
    dsCategoria = models.CharField(max_length=120)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default="DESPESA")

    def __str__(self):
        return self.dsCategoria


class Subcategoria(models.Model):
    cdSubcategoria = models.IntegerField(unique=True, db_index=True)
    cdCategoria = models.ForeignKey(Categoria, on_delete=models.PROTECT)
    dsSubcategoria = models.CharField(max_length=120)

    def __str__(self):
        return self.dsSubcategoria


class ContasPagar(models.Model):
    RECORRENCIA_CHOICES = [
        ("MENSAL", "MENSAL"),
        ("SEMANAL", "SEMANAL"),
        ("ANUAL", "ANUAL"),
    ]
    STATUS_CHOICES = [
        ("AGENDADO", "AGENDADO"),
        ("PAGO", "PAGO"),
        ("ATRASADO", "ATRASADO"),
        ("CANCELADO", "CANCELADO"),
    ]

    cdContasPagar = models.IntegerField(unique=True, db_index=True)
    cdFornecedor = models.ForeignKey(Fornecedor, on_delete=models.PROTECT)
    cdCategoria = models.ForeignKey(Categoria, on_delete=models.PROTECT)
    cdSubcategoria = models.ForeignKey(Subcategoria, on_delete=models.PROTECT)
    dtVencimento = models.DateField()
    dtCadastro = models.DateTimeField(auto_now_add=True)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    recorrencia = models.CharField(max_length=10, choices=RECORRENCIA_CHOICES, blank=True)
    recorrencia_quantidade = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="AGENDADO")
    dtPagamento = models.DateField(null=True, blank=True)
    comprovante = models.FileField(upload_to="comprovantes/contas_pagar", null=True, blank=True)
    motivo_cancelamento = models.TextField(blank=True)

    def __str__(self):
        return f"ContasPagar {self.cdContasPagar}"


class AulaSessao(models.Model):
    unidade = models.ForeignKey(Unidade, on_delete=models.PROTECT)
    tipoServico = models.ForeignKey(TipoServico, on_delete=models.PROTECT)
    profissional = models.ForeignKey(Profissional, on_delete=models.SET_NULL, null=True, blank=True)
    data = models.DateField()
    horaInicio = models.TimeField()
    horaFim = models.TimeField()
    capacidade = models.IntegerField(null=True, blank=True)
    dtCadastro = models.DateTimeField(auto_now_add=True)

    def capacidade_efetiva(self):
        return self.capacidade if self.capacidade is not None else self.unidade.capacidade

    def __str__(self):
        return f"{self.data} {self.horaInicio}"


class Reserva(models.Model):
    STATUS_CHOICES = [
        ("RESERVADA", "RESERVADA"),
        ("CONCLUIDA", "CONCLUIDA"),
        ("FALTOU_AVISOU", "FALTOU_AVISOU"),
        ("FALTOU_SEM_AVISAR", "FALTOU_SEM_AVISAR"),
        ("CANCELADA", "CANCELADA"),
        ("PENDENTE", "PENDENTE"),
    ]

    aluno = models.ForeignKey(Aluno, on_delete=models.PROTECT)
    aulaSessao = models.ForeignKey(AulaSessao, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="RESERVADA")
    dtCadastro = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("aluno", "aulaSessao")

    def clean(self):
        if self.status == "RESERVADA":
            total = Reserva.objects.filter(aulaSessao=self.aulaSessao, status="RESERVADA").exclude(pk=self.pk).count()
            if total >= self.aulaSessao.capacidade_efetiva():
                raise ValidationError("Capacidade excedida")

    def __str__(self):
        return f"Reserva {self.aluno}"


class ModeloEvolucao(models.Model):
    cdModeloEvolucao = models.IntegerField(unique=True, db_index=True)
    titulo = models.CharField(max_length=120)
    texto = models.TextField()
    ativo = models.BooleanField(default=True)
    dtCadastro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo


class EvolucaoAluno(models.Model):
    reserva = models.ForeignKey(Reserva, on_delete=models.CASCADE, related_name="evolucoes")
    profissional = models.ForeignKey(Profissional, on_delete=models.PROTECT)
    texto = models.TextField()
    dtEvolucao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Evolucao {self.reserva_id}"


class ContasReceber(models.Model):
    STATUS_CHOICES = [
        ("ABERTO", "ABERTO"),
        ("PAGO", "PAGO"),
        ("ATRASADO", "ATRASADO"),
        ("CANCELADO", "CANCELADO"),
    ]

    contrato = models.ForeignKey(Contrato, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="ABERTO")
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    dtVencimento = models.DateField()
    competencia = models.CharField(max_length=7, blank=True)
    dtPagamento = models.DateField(null=True, blank=True)
    dtCadastro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ContasReceber {self.contrato_id}"


class ContaBancaria(models.Model):
    cdConta = models.IntegerField(unique=True, db_index=True)
    banco = models.CharField(max_length=120)
    agencia = models.CharField(max_length=20)
    conta = models.CharField(max_length=20)
    saldo_inicial = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    ativo = models.BooleanField(default=True)
    dtCadastro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.banco} {self.agencia}/{self.conta}"


class MovimentoConta(models.Model):
    TIPO_CHOICES = [
        ("ENTRADA", "ENTRADA"),
        ("SAIDA", "SAIDA"),
    ]

    conta = models.ForeignKey(ContaBancaria, on_delete=models.PROTECT, related_name="movimentos")
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    valor = models.DecimalField(max_digits=12, decimal_places=2)
    data = models.DateField()
    descricao = models.CharField(max_length=200, blank=True)
    comprovante = models.FileField(upload_to="comprovantes/movimentos", null=True, blank=True)
    dtCadastro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tipo} {self.valor}"


class ModeloContrato(models.Model):
    cdModeloContrato = models.IntegerField(unique=True, db_index=True)
    dsNome = models.CharField(max_length=120)
    conteudo_html = models.TextField()
    ativo = models.BooleanField(default=True)
    dtCadastro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.dsNome


class EmailConfiguracao(models.Model):
    cdEmail = models.IntegerField(unique=True, db_index=True)
    host = models.CharField(max_length=120)
    porta = models.IntegerField(default=587)
    usuario = models.CharField(max_length=150)
    senha = models.CharField(max_length=150)
    use_tls = models.BooleanField(default=True)
    remetente = models.EmailField()
    ativo = models.BooleanField(default=True)
    dtCadastro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.remetente
