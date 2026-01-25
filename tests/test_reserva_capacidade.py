import pytest
from datetime import date, time
from studiopilates.core import models


@pytest.mark.django_db
def test_reserva_respeita_capacidade():
    perfil = models.PerfilAcesso.objects.create(cdPerfilAcesso=1, dsPerfilAcesso="Padrao")
    prof = models.Profissional.objects.create(cdProfissional=1, profissional="Prof", cdPerfilAcesso=perfil)
    unidade = models.Unidade.objects.create(cdUnidade=1, dsUnidade="Un1", capacidade=1)
    termo = models.TermoUso.objects.create(cdTermoUso=1, dsTermoUso="Termo")
    aluno = models.Aluno.objects.create(cdAluno=1, dsNome="Aluno", dsCPF="52998224725", dsRg="1", cdUnidade=unidade, cdTermoUso=termo)
    aluno2 = models.Aluno.objects.create(cdAluno=2, dsNome="Aluno2", dsCPF="11144477735", dsRg="2", cdUnidade=unidade, cdTermoUso=termo)
    tipo_servico = models.TipoServico.objects.create(cdTipoServico=1, dsTipoServico="Servico")
    aula = models.AulaSessao.objects.create(unidade=unidade, tipoServico=tipo_servico, profissional=prof, data=date.today(), horaInicio=time(8, 0), horaFim=time(9, 0))

    reserva1 = models.Reserva(aluno=aluno, aulaSessao=aula, status="RESERVADA")
    reserva1.full_clean()
    reserva1.save()

    reserva2 = models.Reserva(aluno=aluno2, aulaSessao=aula, status="RESERVADA")
    with pytest.raises(Exception):
        reserva2.full_clean()
