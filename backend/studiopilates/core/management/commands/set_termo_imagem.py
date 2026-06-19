# -*- coding: utf-8 -*-
"""Carrega o Termo de Autorizacao de Uso de Imagem padrao da Mayris no TermoUso.

Uso:
    python manage.py set_termo_imagem                 # se houver 1 termo, atualiza-o; senao lista
    python manage.py set_termo_imagem --id 2          # atualiza o termo de id 2
    python manage.py set_termo_imagem --novo "Termo de Imagem"  # cria um novo
"""
from django.core.management.base import BaseCommand

from studiopilates.core import models

CONTEUDO_HTML = """
<h2 style="text-align:center;">🌿 TERMO DE AUTORIZAÇÃO DE USO DE IMAGEM — MAYRIS STUDIO DE PILATES</h2>

<p>Pelo presente instrumento, eu, <strong>{ALUNO_NOME}</strong>,
CPF nº {ALUNO_CPF}, residente em {ALUNO_ENDERECO},
declaro que <strong>AUTORIZO</strong> o uso da minha imagem e voz ao MAYRIS STUDIO DE PILATES,
inscrito sob CNPJ nº 50.732.875/0001-56, representado por sua fundadora Flávia Grando, para fins
institucionais e comerciais, conforme cláusulas abaixo.</p>

<h4>1. Objeto da Autorização</h4>
<p>Autorizo a captação, reprodução e divulgação da minha imagem, voz e/ou depoimentos em:</p>
<ul>
  <li>fotos</li>
  <li>vídeos</li>
  <li>gravações</li>
  <li>relatos ou testemunhos</li>
  <li>bastidores das aulas</li>
  <li>registros da rotina do estúdio</li>
  <li>campanhas promocionais</li>
  <li>materiais educativos</li>
  <li>conteúdos digitais</li>
</ul>
<p>Tudo conforme a linha editorial e estética da Mayris, que prioriza leveza, respeito, acolhimento e
autenticidade feminina.</p>

<h4>2. Finalidade do Uso da Imagem</h4>
<p>A imagem poderá ser utilizada nas seguintes plataformas e materiais:</p>
<ul>
  <li>Instagram</li>
  <li>Facebook</li>
  <li>WhatsApp e listas de transmissão</li>
  <li>Website e blog da Mayris</li>
  <li>Anúncios digitais (Meta Ads, Google Ads etc.)</li>
  <li>Materiais impressos (folders, banners, cartões, cartazes)</li>
  <li>Aulas e eventos internos</li>
  <li>Eventos externos e parcerias da marca</li>
</ul>
<p>A finalidade desta autorização é divulgação institucional, demonstração de resultados, comunicação
de marca e promoção das atividades relacionadas ao Pilates e aos serviços oferecidos pela Mayris.</p>

<h4>3. Caráter Gratuito</h4>
<p>Declaro que não receberei qualquer remuneração pelo uso da minha imagem e voz, concedendo esta
autorização de maneira totalmente gratuita, consciente e voluntária.</p>

<h4>4. Prazo da Autorização</h4>
<p>Esta autorização é concedida por tempo indeterminado, podendo ser revogada a qualquer momento
mediante solicitação por escrito enviada à gestão da Mayris. Após a solicitação de revogação, a Mayris
terá prazo de 30 dias para interromper o uso da imagem em publicações futuras. Conteúdos já publicados
anteriormente não serão removidos, preservando a integridade do histórico editorial da marca.</p>

<h4>5. Compromisso de Ética e Respeito da Mayris</h4>
<p>A Mayris compromete-se a:</p>
<ul>
  <li>tratar toda imagem com respeito, discrição e sensibilidade;</li>
  <li>não expor a aluna de forma constrangedora;</li>
  <li>manter a estética leve, elegante e acolhedora já característica da marca;</li>
  <li>usar a imagem exclusivamente para os fins previstos neste termo;</li>
  <li>não distorcer, descontextualizar ou prejudicar a integridade pessoal do cliente.</li>
</ul>

<h4>6. Não Exclusividade</h4>
<p>A presente autorização é concedida em caráter não exclusivo, podendo o participante realizar outras
parcerias ou aparições públicas sem conflito com este termo.</p>

<h4>7. Proteção de Dados e Privacidade</h4>
<p>Nenhuma informação pessoal (nome completo, endereço, telefone, dados sensíveis) será divulgada
publicamente sem autorização específica e adicional.</p>

<h4>8. Disposições Gerais</h4>
<ul>
  <li>Este termo segue as normas da Lei nº 9.610/98 (Direitos Autorais) e da Lei Geral de Proteção de
  Dados (LGPD).</li>
  <li>As partes elegem o foro da comarca de Sorocaba – SP para dirimir qualquer conflito.</li>
</ul>

<p style="margin-top:24px;">Sorocaba/SP, {DATA_HOJE}.</p>

<h4>Assinaturas</h4>
<p style="margin-top:32px;">____________________________________________<br/>{ALUNO_NOME}<br/>Assinatura da Aluna</p>
<p style="margin-top:32px;">____________________________________________<br/>Assinatura do Estúdio<br/>
Flávia Grando – Mayris Studio de Pilates</p>
""".strip()


class Command(BaseCommand):
    help = "Carrega o Termo de Uso de Imagem padrao da Mayris no TermoUso."

    def add_arguments(self, parser):
        parser.add_argument("--id", type=int, default=None, help="ID do TermoUso a atualizar")
        parser.add_argument("--novo", type=str, default=None, help="Cria um novo termo com esse nome")

    def handle(self, *args, **options):
        termo_id = options.get("id")
        novo_nome = options.get("novo")

        if novo_nome:
            proximo_cd = (models.TermoUso.objects.order_by("-cdTermoUso").values_list("cdTermoUso", flat=True).first() or 0) + 1
            termo = models.TermoUso.objects.create(
                cdTermoUso=proximo_cd,
                nome=novo_nome,
                dsTermoUso=CONTEUDO_HTML,
            )
            self.stdout.write(self.style.SUCCESS(f"Termo criado: #{termo.id} - {termo.nome}"))
            return

        if termo_id:
            termo = models.TermoUso.objects.filter(pk=termo_id).first()
            if not termo:
                self.stderr.write(self.style.ERROR(f"TermoUso id={termo_id} nao encontrado."))
                return
        else:
            qs = models.TermoUso.objects.all()
            total = qs.count()
            if total == 0:
                self.stderr.write(self.style.ERROR("Nenhum TermoUso cadastrado. Use --novo 'Nome' para criar."))
                return
            if total > 1:
                self.stdout.write("Ha mais de um termo. Rode com --id <id> escolhendo um:")
                for t in qs:
                    self.stdout.write(f"  #{t.id} - {t.nome}")
                return
            termo = qs.first()

        termo.dsTermoUso = CONTEUDO_HTML
        termo.save(update_fields=["dsTermoUso"])
        self.stdout.write(self.style.SUCCESS(f"Termo atualizado: #{termo.id} - {termo.nome}"))
