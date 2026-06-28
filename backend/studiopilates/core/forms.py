from decimal import Decimal

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
            "dsProfissao": "Profissao",
            "dsCPF": "CPF",
            "sem_cpf": "Nao tenho CPF",
            "dsRg": "RG",
            "dsEmail": "Email",
            "foto": "Foto",
            "autoriza_imagem": "Autoriza o uso da imagem?",
            "titulo": "Titulo",
            "arquivo": "Arquivo",
            "descricao": "Descricao",
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
            "estado_civil": "Estado civil",
            "cdProfissao": "Profissao",
            "dtInicioContrato": "Inicio do Contrato",
            "dtFimContrato": "Fim do Contrato",
            "dtInicio": "Inicio",
            "dtFim": "Fim",
            "cdUnidade": "Unidade",
            "cdPlano": "Plano",
            "plano": "Plano",
            "cdTipoServico": "Tipo de Servico",
            "cdProfissional": "Profissional",
            "cdAluno": "Aluno",
            "cdTermoUso": "Termo de Uso",
            "cdEndereco": "Endereco",
            "cdFornecedor": "Fornecedor",
            "cdCategoria": "Categoria",
            "cdSubcategoria": "Subcategoria",
            "subcategoria_receita": "Subcategoria",
            "dtVencimento": "Vencimento",
            "valor": "Valor",
            "valor": "Valor",
            "valor_aula": "Valor por aula",
            "recorrencia": "Recorrencia",
            "recorrencia_quantidade": "Quantidade",
            "aulas_por_semana": "Aulas por semana",
            "duracao_meses": "Duracao (Meses)",
            "duracao": "Duracao",
            "duracao_aula_minutos": "Duracao da Aula (Min)",
            "is_avulso": "Aula avulsa",
            "tipos_servico": "Servicos",
            "conteudo_html": "Conteudo HTML",
            "ativo": "Ativo",
            "valor_parcela": "Valor (Parcela)",
            "valor_total": "Valor Total",
            "modo_pagamento": "Modo de Pagamento",
            "diaSemana": "Dia da Semana",
            "horaInicio": "Hora Inicio",
            "horaFim": "Hora Fim",
            "dataInicio": "Data Inicio",
            "dataFim": "Data Fim",
            "recorrente": "Recorrente",
            "motivo": "Motivo",
            "ativo": "Ativo",
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
            "partner_api_key": "Partner API Key",
            "place_api_key": "Place API Key",
            "place_id": "Place ID",
            "webhook_token": "Webhook Token",
            "criar_aluno_automatico": "Cadastrar aluno automaticamente",
            "somente_dia": "Sincronizar apenas hoje",
        }
        for name, field in self.fields.items():
            is_fk = isinstance(field, forms.ModelChoiceField)
            if (name.startswith("cd") and not is_fk) or name == "user":
                field.required = False
                field.widget = forms.HiddenInput()
            if name == "recorrencia" and self._meta.model is models.Contrato:
                field.disabled = True
                field.required = False
                field.initial = getattr(self.instance, "recorrencia", None) or "MENSAL"
            if name in label_map:
                field.label = label_map[name]
            if isinstance(field.widget, forms.HiddenInput):
                continue
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("class", "form-check-input")
                continue
            if isinstance(field.widget, (forms.SelectMultiple, forms.CheckboxSelectMultiple)):
                field.widget.attrs.setdefault("class", "form-select")
                continue
            if is_fk:
                field.widget.attrs.setdefault("class", "form-select")
            else:
                field.widget.attrs.setdefault("class", "form-control")
            if name == "modo_pagamento":
                field.required = True
            if name == "estado_civil":
                field.widget.attrs["class"] = "form-select"
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
            if name == "valor_total":
                field.widget.attrs["readonly"] = "readonly"
            if name == "data":
                field.widget = forms.DateInput(attrs={"type": "date", "class": "form-control"})
            if name in ("dataInicio", "dataFim"):
                field.widget = forms.DateInput(attrs={"type": "date", "class": "form-control"})
            if name in ("dtInicioContrato", "dtFimContrato"):
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
        fields = [
            "cdAluno",
            "dsNome",
            "dsCPF",
            "sem_cpf",
            "dsRg",
            "dsEmail",
            "foto",
            "autoriza_imagem",
            "status",
            "dtNascimento",
            "estado_civil",
            "cdProfissao",
            "cdUnidade",
            "cdTermoUso",
        ]


class EnderecoAlunoForm(BaseAutoCdForm):
    class Meta:
        model = models.EnderecoAluno
        fields = ["cdEndereco", "cdAluno", "dsLogradouro", "dsNumero", "dsCEP", "dsCidade", "dsBairro"]


class ProfissionalForm(BaseAutoCdForm):
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput,
        label="Senha",
        help_text="Defina a senha de acesso (obrigatoria no cadastro).",
    )
    password_confirm = forms.CharField(
        required=False,
        widget=forms.PasswordInput,
        label="Confirmar senha",
    )

    class Meta:
        model = models.Profissional
        fields = ["cdProfissional", "profissional", "email", "celular", "cdPerfilAcesso", "dtNascimento", "crefito"]

    def clean(self):
        cleaned = super().clean()
        password = (cleaned.get("password") or "").strip()
        password_confirm = (cleaned.get("password_confirm") or "").strip()
        if self.instance.pk is None and not password:
            self.add_error("password", "Informe a senha para criar o usuario.")
        if password or password_confirm:
            if password != password_confirm:
                self.add_error("password_confirm", "As senhas nao conferem.")
        return cleaned


class UnidadeForm(BaseAutoCdForm):
    class Meta:
        model = models.Unidade
        fields = ["cdUnidade", "dsUnidade", "capacidade", "duracao_aula_minutos"]


class PlanoForm(BaseAutoCdForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "categoria_receita" in self.fields:
            self.fields["categoria_receita"].queryset = models.Categoria.objects.filter(tipo="RECEITA")
        if "subcategoria_receita" in self.fields:
            self.fields["subcategoria_receita"].queryset = models.Subcategoria.objects.filter(cdCategoria__tipo="RECEITA")

    class Meta:
        model = models.Plano
        fields = [
            "cdPlano",
            "dsPlano",
            "cdTipoServico",
            "categoria_receita",
            "subcategoria_receita",
            "valor",
            "aulas_por_semana",
            "duracao_meses",
            "recorrencia",
            "is_avulso",
            "modeloContrato",
        ]


class TipoServicoForm(BaseAutoCdForm):
    class Meta:
        model = models.TipoServico
        fields = ["cdTipoServico", "dsTipoServico"]


class HorarioStudioForm(BaseAutoCdForm):
    class Meta:
        model = models.HorarioStudio
        fields = ["cdHorario", "unidade", "tipoServico", "profissional", "diaSemana", "horaInicio", "horaFim", "capacidade"]


class HorarioFuncionamentoForm(BaseAutoCdForm):
    class Meta:
        model = models.HorarioFuncionamento
        fields = ["unidade", "tipos_servico", "diaSemana", "horaInicio", "horaFim", "ativo"]


class TermoUsoForm(BaseAutoCdForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        field = self.fields.get("dsTermoUso")
        if field:
            field.widget.attrs["class"] = "form-control js-wysiwyg-source d-none"

    class Meta:
        model = models.TermoUso
        fields = ["nome", "dsTermoUso"]

    def save(self, commit=True):
        obj = super().save(commit=False)
        if not obj.cdTermoUso:
            ultimo = models.TermoUso.objects.order_by("-cdTermoUso").values_list("cdTermoUso", flat=True).first() or 0
            obj.cdTermoUso = ultimo + 1
        if commit:
            obj.save()
        return obj


class ContratoForm(BaseAutoCdForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        plano_field = self.fields.get("cdPlano")
        if plano_field:
            plano_field.queryset = models.Plano.objects.filter(is_avulso=False)
        for name in ("valor_aula", "valor_parcela", "valor_total"):
            field = self.fields.get(name)
            if field:
                field.required = False
        field = self.fields.get("recorrencia")
        if field:
            field.required = False

    def clean(self):
        cleaned = super().clean()
        plano = cleaned.get("cdPlano")
        if not plano:
            return cleaned

        recorrencia = getattr(plano, "recorrencia", "MENSAL") or "MENSAL"
        valor_plano = Decimal(str(getattr(plano, "valor", 0) or 0))
        cleaned["recorrencia"] = recorrencia

        if recorrencia == "SEMANAL":
            valor_aula_raw = cleaned.get("valor_aula")
            try:
                valor_aula = Decimal(str(valor_aula_raw)) if valor_aula_raw not in (None, "") else valor_plano
            except Exception:
                valor_aula = valor_plano
            cleaned["valor_aula"] = valor_aula
            cleaned["valor_parcela"] = valor_aula * Decimal("4")
            cleaned["valor_total"] = cleaned["valor_parcela"]
        else:
            cleaned["valor_aula"] = None
            cleaned["valor_parcela"] = valor_plano
            cleaned["valor_total"] = valor_plano
        return cleaned

    class Meta:
        model = models.Contrato
        fields = [
            "cdContrato",
            "cdAluno",
            "cdPlano",
            "recorrencia",
            "valor_aula",
            "cdUnidade",
            "cdProfissional",
            "modo_pagamento",
            "valor_parcela",
            "valor_total",
            "dtInicioContrato",
            "dtFimContrato",
        ]


class AulaAvulsaForm(BaseAutoCdForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        plano_field = self.fields.get("plano")
        if plano_field:
            plano_field.queryset = models.Plano.objects.filter(is_avulso=True)
        for name in ("recorrencia", "valor_aula", "valor_total"):
            field = self.fields.get(name)
            if field:
                field.required = False

    class Meta:
        model = models.AulaAvulsa
        fields = [
            "cdAulaAvulsa",
            "aluno",
            "plano",
            "recorrencia",
            "quantidade",
            "valor_aula",
            "valor_total",
            "unidade",
            "profissional",
            "dtInicio",
            "dtFim",
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


class BloqueioAgendaForm(BaseAutoCdForm):
    class Meta:
        model = models.BloqueioAgenda
        fields = [
            "unidade",
            "tipoServico",
            "profissional",
            "recorrente",
            "diaSemana",
            "dataInicio",
            "dataFim",
            "horaInicio",
            "horaFim",
            "motivo",
            "ativo",
        ]


class ReservaForm(BaseAutoCdForm):
    class Meta:
        model = models.Reserva
        fields = ["aluno", "aulaSessao", "status"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # O <select> de aulaSessao e renderizado uma vez por reserva na ficha do
        # aluno. Carregar TODAS as aulaSessoes em cada um faz a renderizacao
        # explodir (M reservas x N sessoes) -> WORKER TIMEOUT. O <select> so serve
        # para guardar o valor selecionado (o JS preenche as opcoes via reserva_slots),
        # entao limitamos o queryset a aula atual e, em POST, a aula escolhida.
        field = self.fields.get("aulaSessao")
        if field is not None:
            ids = set()
            if self.instance and self.instance.aulaSessao_id:
                ids.add(self.instance.aulaSessao_id)
            if self.is_bound:
                submitted = self.data.get(self.add_prefix("aulaSessao"))
                if submitted:
                    try:
                        ids.add(int(submitted))
                    except (TypeError, ValueError):
                        pass
            field.queryset = (
                models.AulaSessao.objects.filter(pk__in=ids) if ids else models.AulaSessao.objects.none()
            )


class ContasReceberForm(BaseAutoCdForm):
    class Meta:
        model = models.ContasReceber
        fields = ["contrato", "status", "valor", "dtVencimento", "competencia"]


class LancamentoAvulsoForm(BaseAutoCdForm):
    """Lancamento financeiro avulso na ficha do aluno (sem contrato nem aula)."""

    class Meta:
        model = models.ContasReceber
        fields = ["descricao", "valor", "dtVencimento", "competencia", "status"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["descricao"].required = True
        self.fields["descricao"].widget.attrs["placeholder"] = "Ex.: Taxa de matricula, venda de produto..."
        self.fields["competencia"].widget.attrs.setdefault("placeholder", "AAAA-MM")
        self.fields["competencia"].label = "Competencia"


class PerfilAcessoForm(BaseAutoCdForm):
    class Meta:
        model = models.PerfilAcesso
        fields = ["cdPerfilAcesso", "dsPerfilAcesso"]


class ProfissaoForm(BaseAutoCdForm):
    class Meta:
        model = models.Profissao
        fields = ["cdProfissao", "dsProfissao"]


class ModeloContratoForm(BaseAutoCdForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        field = self.fields.get("conteudo_html")
        if field:
            field.widget.attrs["class"] = "form-control js-wysiwyg-source d-none"

    class Meta:
        model = models.ModeloContrato
        fields = ["dsNome", "conteudo_html", "ativo"]

    def save(self, commit=True):
        obj = super().save(commit=False)
        if not obj.cdModeloContrato:
            ultimo = models.ModeloContrato.objects.order_by("-cdModeloContrato").values_list("cdModeloContrato", flat=True).first() or 0
            obj.cdModeloContrato = ultimo + 1
        if commit:
            obj.save()
        return obj


class EmailConfiguracaoForm(BaseAutoCdForm):
    class Meta:
        model = models.EmailConfiguracao
        fields = ["cdEmail", "host", "porta", "usuario", "senha", "use_tls", "remetente", "ativo"]


class WhatsappConfiguracaoForm(BaseAutoCdForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        url_field = self.fields.get("evolution_url")
        if url_field:
            url_field.label = "URL da WasenderAPI"
            url_field.widget.attrs["readonly"] = True
            if not url_field.initial and self.instance and getattr(self.instance, "evolution_url", ""):
                url_field.initial = self.instance.evolution_url
            if not url_field.initial:
                url_field.initial = "https://www.wasenderapi.com/api/send-message"
        token_field = self.fields.get("evolution_senha")
        if token_field:
            token_field.label = "Token (API Key)"
            token_field.widget.attrs["placeholder"] = "Cole aqui o token da WasenderAPI"
        usuario_field = self.fields.get("evolution_usuario")
        if usuario_field:
            usuario_field.label = "Usuario (nao usado)"
            usuario_field.widget.attrs["readonly"] = True
        acompanhar_field = self.fields.get("acompanhar_envios")
        if acompanhar_field:
            acompanhar_field.label = "Receber resumo dos envios no meu WhatsApp"
        numero_field = self.fields.get("numero_acompanhamento")
        if numero_field:
            numero_field.label = "Meu numero (acompanhamento)"
            numero_field.widget.attrs["placeholder"] = "Ex.: 5511999999999"

    class Meta:
        model = models.WhatsappConfiguracao
        fields = [
            "evolution_url",
            "evolution_senha",
            "acompanhar_envios",
            "numero_acompanhamento",
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
            "avisar_aniversario",
            "horario_aviso_aniversario",
            "template_aniversario",
            "avisar_fim_contrato",
            "template_fim_contrato",
            "avisar_vencimento",
            "horario_aviso_vencimento",
            "template_vencimento_proximo",
            "avisar_atraso",
            "horario_aviso_atraso",
            "template_mensalidade_atraso",
            "avisar_tres_meses",
            "horario_aviso_tres_meses",
            "template_tres_meses",
            "variaveis_template",
        ]


class AvisoAlunoConfigForm(BaseAutoCdForm):
    """Config so do Aviso ao aluno (tela dedicada)."""

    class Meta:
        model = models.WhatsappConfiguracao
        fields = [
            "avisar_aluno",
            "horario_aviso_aluno",
            "template_aviso_aluno",
            "acompanhar_envios",
            "numero_acompanhamento",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "avisar_aluno" in self.fields:
            self.fields["avisar_aluno"].label = "Habilitar agendamento automatico"
        if "horario_aviso_aluno" in self.fields:
            self.fields["horario_aviso_aluno"].label = "Horario do envio automatico"
        if "template_aviso_aluno" in self.fields:
            self.fields["template_aviso_aluno"].label = "Mensagem"
            self.fields["template_aviso_aluno"].widget.attrs["rows"] = 5
        if "acompanhar_envios" in self.fields:
            self.fields["acompanhar_envios"].label = "Receber resumo no meu WhatsApp"
        if "numero_acompanhamento" in self.fields:
            self.fields["numero_acompanhamento"].label = "Meu numero (acompanhamento)"
            self.fields["numero_acompanhamento"].widget.attrs["placeholder"] = "5511999999999"


class TotalpassConfiguracaoForm(BaseAutoCdForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        api_fields = ["partner_api_key", "place_api_key", "webhook_token"]
        for name in api_fields:
            field = self.fields.get(name)
            if field:
                field.widget = forms.PasswordInput(render_value=True, attrs={"class": "form-control"})
        place_id = self.fields.get("place_id")
        if place_id:
            place_id.widget.attrs["placeholder"] = "ID do place no TotalPass"

    class Meta:
        model = models.TotalpassConfiguracao
        fields = [
            "ativo",
            "partner_api_key",
            "place_api_key",
            "place_id",
            "webhook_token",
            "criar_aluno_automatico",
            "somente_dia",
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


class AlunoDocumentoForm(BaseAutoCdForm):
    class Meta:
        model = models.AlunoDocumento
        fields = ["cdDocumento", "titulo", "arquivo", "descricao"]


class WhatsappMessageForm(forms.Form):
    mensagem = forms.CharField(
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Escreva a mensagem que será enviada por WhatsApp"}),
        label="Mensagem de WhatsApp",
    )


class IntegracaoTokenForm(forms.ModelForm):
    class Meta:
        model = models.IntegracaoToken
        fields = ["nome", "ativo"]
        labels = {"nome": "Empresa / Descricao", "ativo": "Ativo"}
        widgets = {
            "nome": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex: Empresa XPTO"}),
            "ativo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
