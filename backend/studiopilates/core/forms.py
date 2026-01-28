from django import forms
from . import models


class BaseAutoCdForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        label_map = {
            "dsNome": "Nome",
            "dsPlano": "Plano",
            "dsUnidade": "Unidade",
            "dsTipoPlano": "Tipo de Plano",
            "dsTipoServico": "Tipo de Servico",
            "dsTermoUso": "Termo de Uso",
            "nome": "Nome",
            "dsPerfilAcesso": "Perfil de Acesso",
            "dsFornecedor": "Fornecedor",
            "dsCategoria": "Categoria",
            "tipo": "Tipo",
            "dsSubcategoria": "Subcategoria",
            "dsCPF": "CPF",
            "dsRg": "RG",
            "dsEmail": "Email",
            "foto": "Foto",
            "dsLogradouro": "Logradouro",
            "dsNumero": "Numero",
            "dsCEP": "CEP",
            "dsCidade": "Cidade",
            "dsBairro": "Bairro",
            "profissional": "Profissional",
            "email": "Email",
            "celular": "Celular",
            "crefito": "Crefito",
            "dtNascimento": "Data de Nascimento",
            "dtInicioContrato": "Inicio do Contrato",
            "dtFimContrato": "Fim do Contrato",
            "cdUnidade": "Unidade",
            "cdPlano": "Plano",
            "cdTipoServico": "Tipo de Servico",
            "cdProfissional": "Profissional",
            "cdAluno": "Aluno",
            "cdTermoUso": "Termo de Uso",
            "cdEndereco": "Endereco",
            "cdFornecedor": "Fornecedor",
            "cdCategoria": "Categoria",
            "cdSubcategoria": "Subcategoria",
            "dtVencimento": "Vencimento",
            "valor": "Valor",
            "valor": "Valor",
            "recorrencia": "Recorrencia",
            "recorrencia_quantidade": "Quantidade",
            "aulas_por_semana": "Aulas por semana",
            "duracao_meses": "Duracao (Meses)",
            "duracao": "Duracao",
            "duracao_aula_minutos": "Duracao da Aula (Min)",
            "conteudo_html": "Conteudo HTML",
            "ativo": "Ativo",
            "valor_parcela": "Valor (Parcela)",
            "valor_total": "Valor Total",
            "diaSemana": "Dia da Semana",
            "horaInicio": "Hora Inicio",
            "horaFim": "Hora Fim",
            "capacidade": "Capacidade",
            "tipoServico": "Tipo de Servico",
            "unidade": "Unidade",
            "titulo": "Titulo",
            "texto": "Texto",
            "banco": "Banco",
            "agencia": "Agencia",
            "conta": "Conta",
            "saldo_inicial": "Saldo Inicial",
            "tipo": "Tipo",
            "data": "Data",
            "descricao": "Descricao",
            "host": "Servidor SMTP",
            "porta": "Porta",
            "usuario": "Usuario",
            "senha": "Senha",
            "use_tls": "Usar TLS",
            "remetente": "Email Remetente",
        }
        for name, field in self.fields.items():
            is_fk = isinstance(field, forms.ModelChoiceField)
            if (name.startswith("cd") and not is_fk) or name == "user":
                field.required = False
                field.widget = forms.HiddenInput()
            if name in label_map:
                field.label = label_map[name]
            if isinstance(field.widget, forms.HiddenInput):
                continue
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("class", "form-check-input")
                continue
            if is_fk:
                field.widget.attrs.setdefault("class", "form-select")
            else:
                field.widget.attrs.setdefault("class", "form-control")
            if name == "dsCPF":
                field.widget.attrs["class"] = "form-control js-cpf"
                field.widget.attrs["placeholder"] = "000.000.000-00"
            if name == "dsEmail":
                field.widget.attrs["type"] = "email"
            if name == "email":
                field.widget.attrs["type"] = "email"
            if name == "dtNascimento":
                field.widget = forms.DateInput(attrs={"type": "date", "class": "form-control js-date", "placeholder": "dd/mm/aaaa"})
            if name == "dtVencimento":
                field.widget = forms.DateInput(attrs={"type": "date", "class": "form-control"})
            if name == "data":
                field.widget = forms.DateInput(attrs={"type": "date", "class": "form-control"})
            if name == "senha":
                field.widget = forms.PasswordInput(render_value=True, attrs={"class": "form-control"})
            if name in ("horaInicio", "horaFim"):
                field.widget = forms.TimeInput(attrs={"type": "time", "class": "form-control"})
            if name == "diaSemana":
                field.widget.attrs["class"] = "form-select"


class AlunoForm(BaseAutoCdForm):
    class Meta:
        model = models.Aluno
        fields = ["cdAluno", "dsNome", "dsCPF", "dsRg", "dsEmail", "foto", "dtNascimento", "cdUnidade", "cdTermoUso"]


class EnderecoAlunoForm(BaseAutoCdForm):
    class Meta:
        model = models.EnderecoAluno
        fields = ["cdEndereco", "cdAluno", "dsLogradouro", "dsNumero", "dsCEP", "dsCidade", "dsBairro"]


class ProfissionalForm(BaseAutoCdForm):
    password = forms.CharField(required=False, widget=forms.PasswordInput)

    class Meta:
        model = models.Profissional
        fields = ["cdProfissional", "profissional", "email", "celular", "cdPerfilAcesso", "dtNascimento", "crefito"]


class UnidadeForm(BaseAutoCdForm):
    class Meta:
        model = models.Unidade
        fields = ["cdUnidade", "dsUnidade", "capacidade", "duracao_aula_minutos"]


class PlanoForm(BaseAutoCdForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "categoria_receita" in self.fields:
            self.fields["categoria_receita"].queryset = models.Categoria.objects.filter(tipo="RECEITA")

    class Meta:
        model = models.Plano
        fields = ["cdPlano", "dsPlano", "cdTipoServico", "categoria_receita", "valor", "aulas_por_semana", "duracao_meses", "modeloContrato"]


class TipoServicoForm(BaseAutoCdForm):
    class Meta:
        model = models.TipoServico
        fields = ["cdTipoServico", "dsTipoServico"]


class HorarioStudioForm(BaseAutoCdForm):
    class Meta:
        model = models.HorarioStudio
        fields = ["cdHorario", "unidade", "tipoServico", "profissional", "diaSemana", "horaInicio", "horaFim", "capacidade"]


class TermoUsoForm(BaseAutoCdForm):
    class Meta:
        model = models.TermoUso
        fields = ["cdTermoUso", "nome", "dsTermoUso"]


class ContratoForm(BaseAutoCdForm):
    class Meta:
        model = models.Contrato
        fields = [
            "cdContrato",
            "cdAluno",
            "cdPlano",
            "cdUnidade",
            "cdProfissional",
            "valor_parcela",
            "valor_total",
            "dtInicioContrato",
            "dtFimContrato",
        ]


class FornecedorForm(BaseAutoCdForm):
    class Meta:
        model = models.Fornecedor
        fields = ["cdFornecedor", "dsFornecedor"]


class CategoriaForm(BaseAutoCdForm):
    class Meta:
        model = models.Categoria
        fields = ["cdCategoria", "dsCategoria", "tipo"]


class SubcategoriaForm(BaseAutoCdForm):
    class Meta:
        model = models.Subcategoria
        fields = ["cdSubcategoria", "cdCategoria", "dsSubcategoria"]


class ContasPagarForm(BaseAutoCdForm):
    class Meta:
        model = models.ContasPagar
        fields = ["cdContasPagar", "cdFornecedor", "cdCategoria", "cdSubcategoria", "dtVencimento", "valor", "recorrencia", "recorrencia_quantidade"]


class AulaSessaoForm(BaseAutoCdForm):
    class Meta:
        model = models.AulaSessao
        fields = ["unidade", "tipoServico", "profissional", "data", "horaInicio", "horaFim", "capacidade"]


class ReservaForm(BaseAutoCdForm):
    class Meta:
        model = models.Reserva
        fields = ["aluno", "aulaSessao", "status"]


class ContasReceberForm(BaseAutoCdForm):
    class Meta:
        model = models.ContasReceber
        fields = ["contrato", "status", "valor", "dtVencimento", "competencia"]


class PerfilAcessoForm(BaseAutoCdForm):
    class Meta:
        model = models.PerfilAcesso
        fields = ["cdPerfilAcesso", "dsPerfilAcesso"]


class ModeloContratoForm(BaseAutoCdForm):
    class Meta:
        model = models.ModeloContrato
        fields = ["cdModeloContrato", "dsNome", "conteudo_html", "ativo"]


class EmailConfiguracaoForm(BaseAutoCdForm):
    class Meta:
        model = models.EmailConfiguracao
        fields = ["cdEmail", "host", "porta", "usuario", "senha", "use_tls", "remetente", "ativo"]


class WhatsappConfiguracaoForm(BaseAutoCdForm):
    class Meta:
        model = models.WhatsappConfiguracao
        fields = [
            "evolution_url",
            "evolution_usuario",
            "evolution_senha",
            "avisar_aluno",
            "horario_aviso_aluno",
            "template_aviso_aluno",
            "avisar_professor",
            "horario_aviso_professor",
            "template_aviso_professor",
            "enviar_link_contrato",
            "template_link_contrato",
            "avisar_renovacao",
            "horario_aviso_renovacao",
            "template_aviso_renovacao",
            "variaveis_template",
        ]


class ModeloEvolucaoForm(BaseAutoCdForm):
    class Meta:
        model = models.ModeloEvolucao
        fields = ["cdModeloEvolucao", "titulo", "texto", "ativo"]


class ContaBancariaForm(BaseAutoCdForm):
    class Meta:
        model = models.ContaBancaria
        fields = ["cdConta", "banco", "agencia", "conta", "saldo_inicial", "ativo"]


class MovimentoContaForm(BaseAutoCdForm):
    class Meta:
        model = models.MovimentoConta
        fields = ["conta", "tipo", "valor", "data", "descricao", "comprovante"]


class WhatsappMessageForm(forms.Form):
    mensagem = forms.CharField(
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Escreva a mensagem que será enviada por WhatsApp"}),
        label="Mensagem de WhatsApp",
    )
