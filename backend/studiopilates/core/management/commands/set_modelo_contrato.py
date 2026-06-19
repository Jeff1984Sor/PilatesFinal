# -*- coding: utf-8 -*-
"""Carrega o contrato padrao do Studio Mayris no ModeloContrato (conteudo_html),
ja com as variaveis do sistema ({ALUNO_NOME}, {CONTRATO_VALOR_PARCELA}, ...).

Uso:
    python manage.py set_modelo_contrato            # se houver 1 modelo, atualiza-o; senao lista
    python manage.py set_modelo_contrato --id 3     # atualiza o modelo de id 3
    python manage.py set_modelo_contrato --novo "Contrato Padrao Mayris"  # cria um novo
"""
from django.core.management.base import BaseCommand

from studiopilates.core import models

CONTEUDO_HTML = """
<h2 style="text-align:center;">CONTRATO DE PRESTAÇÃO DE SERVIÇOS</h2>

<p><strong>Contratado:</strong> Studio Mayris Pilates Sorocaba, por Flávia de Barros Grando,
endereço na Avenida Artur Bernardes, 1079, Vila Gabriel, Sorocaba/SP, neste ato representada
por Flávia de Barros Grando, CPF nº 307.866.128-86, Fisioterapeuta e Instrutora de Pilates
Crefito-3 nº 79013-F.</p>

<p><strong>Contratante (Aluno):</strong><br/>
Nome: {ALUNO_NOME}<br/>
Endereço: {ALUNO_ENDERECO}<br/>
RG: {ALUNO_RG} &nbsp;&nbsp; CPF: {ALUNO_CPF} &nbsp;&nbsp; DN: {ALUNO_NASCIMENTO}<br/>
Telefone/Celular: {ALUNO_TELEFONE}<br/>
E-mail: {ALUNO_EMAIL}<br/>
Profissão: {ALUNO_PROFISSAO} &nbsp;&nbsp; Estado Civil: {ALUNO_ESTADO_CIVIL}</p>

<p>As partes identificadas acima têm, entre si, justas e acertadas o presente Contrato de
Prestação de Serviços:</p>

<p><strong>DO OBJETO</strong></p>
<p><strong>CLÁUSULA 1ª</strong> - Este contrato tem como objeto o serviço profissional de pilates
especializado, além do uso do espaço físico, bem como seus equipamentos, acessórios e suas
dependências, para prática do exercício, pelo contratante realizar a sessão personalizada.</p>

<p><strong>DO FUNCIONAMENTO DAS SESSÕES</strong></p>
<p><strong>CLÁUSULA 2ª</strong> - A prestação de serviços ocorrerá com horários pré-agendados, no ato
da matrícula, de segunda a sexta-feira, exceto feriados nacionais e municipais, de acordo com a
disponibilidade de horários do CONTRATADO, com duração de 50 minutos.</p>
<p><strong>CLÁUSULA 3ª</strong> - O contratante deve estar ciente de que para obter resultados
benéficos é necessário ter disciplina e frequência nos atendimentos sob orientação do responsável.</p>

<p><strong>DOS HORÁRIOS DAS ATIVIDADES</strong></p>
<p><strong>CLÁUSULA 4ª</strong> - O contratante e a contratada firmam entre si e agendam os horários
semanais para a realização das sessões, conforme a cláusula 2ª, e conforme a quantidade de aulas
contratadas.</p>
<p><strong>CLÁUSULA 5ª</strong> - Será considerado atraso quando o Aluno ultrapassar os 10 (dez)
minutos iniciais do seu horário agendado e não será compensado da duração total da aula.</p>
<p>A justificativa de ausência da aula deve ser no mínimo de 6 HORAS, reposta dentro do seu período
de 30 dias mensal nos horários e dias disponíveis; caso contrário, a ausência acarretará a
impossibilidade de reposição da sessão, salvo justo motivo comprovado com atestado médico e desde
que haja disponibilidade de horários.</p>
<p>5.1 – Na ausência de comunicação dentro do prazo estipulado, o atendimento/sessão será contado
como realizado;</p>
<p>5.2 - Caso o CONTRATANTE não retornar às sessões sem prévio aviso, perderá o direito ao seu
horário e validade da sua matrícula, sendo cobrado o valor mensal que tiver pago.</p>
<p>5.3 - A quantidade de reposições será proporcional ao número de sessões mensais que faltar dentro
daquele mês.</p>

<p><strong>CLÁUSULA 6ª</strong> - A escolha do Plano pelo Contratante e seu pagamento serão realizados
na data de matrícula, com renovação programada para a última sessão programada.</p>
<p><strong>CLÁUSULA 7ª</strong> - O CONTRATANTE pagará o valor mensal de R$ {CONTRATO_VALOR_PARCELA},
referente ao plano <strong>{PLANO_NOME}</strong> ({PLANO_AULAS_SEMANA} aula(s) por semana).</p>
<p>O modo de pagamento será feito através de: {CONTRATO_MODO_PAGAMENTO}.</p>
<p>7.1 - Ao Plano {PLANO_NOME}.</p>
<p>7.2 - Não ocorrendo o pagamento do serviço até no máximo dois dias da data estipulada, o débito
será incrementado de multa de 10% do valor mensal.</p>
<p>7.3 - O pagamento corresponderá à quantidade de sessões realizadas no seu período mês, de acordo
com a quantidade de sessões à escolha do Plano.</p>
<p>7.4 - Os reajustes ocorrerão 01 vez ao ano e será acrescido o percentual de 5% mais o índice
acumulado do IGPM (índice geral de preços no mercado).</p>
<p><strong>CLÁUSULA 8ª</strong> - As sessões que caírem em feriados nacionais e municipais não serão
descontadas do valor da mensalidade.</p>
<p>8.1 - O feriado de carnaval incluirá a segunda e terça, comunicado e ajustado previamente.</p>

<p><strong>CLÁUSULA 9ª</strong> - Em casos excepcionais ou por questões médicas, o contratado poderá
se ausentar e colocar outro profissional designado, devidamente habilitado e capacitado, para que o
Aluno mantenha seu horário de aulas sem prejuízos.</p>
<p><strong>CLÁUSULA 10ª</strong> - Não haverá restituição de pagamento referente ao período em que o
contratado se ausentar, cabendo somente a possibilidade de reposição dos atendimentos.</p>
<p><strong>CLÁUSULA 11ª</strong> - Excepcionalmente nos meses de dezembro e janeiro, haverá férias
coletivas, cabendo à contratada estipular de 15 a 20 dias, compreendido entre o natal e ano novo, com
dever de comunicar antecipadamente o contratante.</p>

<p><strong>DA DURAÇÃO E RESCISÃO DO CONTRATO</strong></p>
<p><strong>CLÁUSULA 12ª</strong> - O presente contrato será por tempo determinado de
{PLANO_DURACAO_MESES} mês(es), com início em {CONTRATO_INICIO} e término em {CONTRATO_FIM}, com
reajuste dos valores no mês de ABRIL de acordo com a cláusula 7.4.</p>
<p>12.1 - Em relação aos planos longos, se o CONTRATADO rescindir o plano escolhido, haverá cobrança
de multa de 30% do valor integral do plano, e os meses já pagos serão cobrados como se não houvesse
dado o desconto pelo plano.</p>
<p><strong>CLÁUSULA 13ª</strong> - Não havendo o pagamento antecipado, não haverá reserva dos dias e
horários.</p>
<p><strong>CLÁUSULA 14ª</strong> - Fica a critério da CONTRATADA a execução e cobrança judicial a
partir do 45º dia de atraso, vencendo-se antecipadamente todo o contrato e, a CONTRATANTE fica desde
já ciente:</p>
<p>A) Inclusão do nome do CONTRATANTE no SPC e SERASA.<br/>
B) Ajuizar Ação Monitória ou Ação de Execução.</p>
<p><strong>CLÁUSULA 15ª</strong> - No caso de atraso no pagamento, esse será encaminhado ao cartório
de títulos e protestos, sendo obrigação do(a) aluno(a) realizar a negociação com o Studio, pagar e,
após a sua compensação, solicitar a carta de quitação. Com o recebimento da carta de quitação o aluno
deve ir até o cartório de títulos e protestos, apresentar a documentação e pagar os emolumentos para
que assim ocorra a baixa do título. Por fim, necessário esclarecer que essa é uma obrigação legal
assumida pelo aluno, que pactua o presente contrato nessa modalidade e que deu motivo à causa, uma vez
que não pagou na data acordada a obrigação assumida.</p>
<p><strong>CLÁUSULA 16ª</strong> - A elaboração e execução dos programas de aulas serão realizadas
exclusivamente pelos instrutores da CONTRATADA, sendo vedada a prática de qualquer atividade física
dentro das suas dependências sem o acompanhamento de um profissional autorizado pela CONTRATADA.</p>
<p><strong>CLÁUSULA 17ª</strong> - O CLIENTE deverá desenvolver os exercícios sempre com a orientação
do instrutor para evitar acidentes, dos quais a CONTRATADA não se responsabilizará por contusões ou
acidentes decorrentes da atividade física dentro de suas dependências.</p>
<p><strong>CLÁUSULA 18ª</strong> - Eventualmente, a CONTRATADA fará fotos e vídeos de suas aulas e
eventos e poderá publicar a divulgação de imagens, textos e áudios em seu site e mídias sociais, desde
já previamente autorizado pelo cliente, conforme a resolução nº 532/2021-COFFITO. &nbsp; ( ) Sim
&nbsp; ( ) Não</p>
<p><strong>CLÁUSULA 19ª</strong> - As partes deste contrato têm o dever de comunicar sobre eventuais
suspeitas de doença contagiosa, devendo, antes do seu retorno, apresentar atestado ou documento que
garanta a integridade física sua e para terceiros, conforme o Código Penal art. 268 - Infringir
determinação do poder público destinada a impedir introdução ou propagação de doença contagiosa:
Pena - detenção, de um mês a um ano, e multa.</p>
<p><strong>CLÁUSULA 20ª</strong> - As partes elegem o foro da Comarca de Sorocaba/SP como o competente
para dirimir qualquer controvérsia ou litígio oriundos do presente contrato, com renúncia a qualquer
outro.</p>
<p><strong>CLÁUSULA 21ª</strong> - E, por estarem justas e CONTRATADAS, assinam este instrumento em 2
(duas) vias de igual teor e forma, para produzir um único efeito. Está pactuado, portanto, o termo
presente, reconhecendo-o e prometendo cumpri-lo fiel e cabalmente.</p>

<p style="margin-top:24px;">Sorocaba/SP, {DATA_HOJE}.</p>

<table style="width:100%; margin-top:48px;">
  <tr>
    <td style="text-align:center; width:50%;">_______________________________<br/>{ALUNO_NOME}<br/>Assinatura do Aluno</td>
    <td style="text-align:center; width:50%;">_______________________________<br/>Mayris Pilates<br/>CNPJ 50.732.875/0001-56</td>
  </tr>
</table>
""".strip()


class Command(BaseCommand):
    help = "Carrega o contrato padrao do Studio Mayris no ModeloContrato."

    def add_arguments(self, parser):
        parser.add_argument("--id", type=int, default=None, help="ID do ModeloContrato a atualizar")
        parser.add_argument("--novo", type=str, default=None, help="Cria um novo modelo com esse nome")

    def handle(self, *args, **options):
        modelo_id = options.get("id")
        novo_nome = options.get("novo")

        if novo_nome:
            proximo_cd = (models.ModeloContrato.objects.order_by("-cdModeloContrato").values_list("cdModeloContrato", flat=True).first() or 0) + 1
            modelo = models.ModeloContrato.objects.create(
                cdModeloContrato=proximo_cd,
                dsNome=novo_nome,
                conteudo_html=CONTEUDO_HTML,
                ativo=True,
            )
            self.stdout.write(self.style.SUCCESS(f"Modelo criado: #{modelo.id} - {modelo.dsNome}"))
            return

        if modelo_id:
            modelo = models.ModeloContrato.objects.filter(pk=modelo_id).first()
            if not modelo:
                self.stderr.write(self.style.ERROR(f"ModeloContrato id={modelo_id} nao encontrado."))
                return
        else:
            qs = models.ModeloContrato.objects.all()
            total = qs.count()
            if total == 0:
                self.stderr.write(self.style.ERROR("Nenhum ModeloContrato cadastrado. Use --novo 'Nome' para criar."))
                return
            if total > 1:
                self.stdout.write("Ha mais de um modelo. Rode com --id <id> escolhendo um:")
                for m in qs:
                    self.stdout.write(f"  #{m.id} - {m.dsNome}")
                return
            modelo = qs.first()

        modelo.conteudo_html = CONTEUDO_HTML
        modelo.save(update_fields=["conteudo_html"])
        self.stdout.write(self.style.SUCCESS(f"Modelo atualizado: #{modelo.id} - {modelo.dsNome}"))
