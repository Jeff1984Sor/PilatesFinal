from app.modules.planos.repository import RecorrenciaRepository, TipoPlanoRepository, TipoServicoRepository, PlanoRepository


class PlanosService:
    def __init__(self, recorrencia: RecorrenciaRepository, tipo_plano: TipoPlanoRepository, tipo_servico: TipoServicoRepository, plano: PlanoRepository):
        self.recorrencia = recorrencia
        self.tipo_plano = tipo_plano
        self.tipo_servico = tipo_servico
        self.plano = plano
