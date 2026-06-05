from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException, status
from sqlalchemy import select, func, case
from sqlalchemy.orm import Session

from app.modules.comissoes.models import Comissao, ComissaoStatus
from app.modules.financeiro.models import ContasReceber, ContaStatus
from app.modules.contratos.models import Contrato
from app.modules.profissionais.models import Profissional


def parse_competencia(competencia: str) -> tuple[date, date]:
    """Recebe 'YYYY-MM' e devolve (primeiro_dia, primeiro_dia_mes_seguinte)."""
    try:
        ano, mes = competencia.split("-")
        ano, mes = int(ano), int(mes)
        inicio = date(ano, mes, 1)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="competencia invalida (use YYYY-MM)")
    if mes == 12:
        fim = date(ano + 1, 1, 1)
    else:
        fim = date(ano, mes + 1, 1)
    return inicio, fim


def _q2(value) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class ComissaoService:
    def __init__(self, db: Session):
        self.db = db

    def gerar(self, competencia: str) -> dict:
        inicio, fim = parse_competencia(competencia)

        # percentual de comissao por profissional (tabela pequena, carrega tudo)
        percentual_por_prof = {
            pid: perc
            for pid, perc in self.db.execute(
                select(Profissional.id, Profissional.comissao_percentual)
            ).all()
        }

        # recebimentos pagos no periodo. LEFT JOIN no contrato para tambem cobrir
        # aulas avulsas (sem contrato), que trazem o profissional direto no recebimento.
        stmt = (
            select(ContasReceber, Contrato.profissional_id)
            .outerjoin(Contrato, ContasReceber.contrato_id == Contrato.id)
            .where(ContasReceber.status == ContaStatus.pago.value)
            .where(ContasReceber.recebido_em >= inicio)
            .where(ContasReceber.recebido_em < fim)
        )
        rows = [
            (conta, conta.profissional_id or contrato_prof_id)
            for conta, contrato_prof_id in self.db.execute(stmt).all()
        ]

        # contas que ja possuem comissao gerada
        ja_geradas = set(
            self.db.execute(
                select(Comissao.conta_receber_id).where(Comissao.conta_receber_id.isnot(None))
            ).scalars().all()
        )

        geradas = 0
        total = Decimal("0.00")
        for conta, profissional_id in rows:
            if conta.id in ja_geradas:
                continue
            if not profissional_id:
                continue
            percentual = percentual_por_prof.get(profissional_id)
            if not percentual or Decimal(str(percentual)) <= 0:
                continue
            valor_base = _q2(conta.valor)
            perc = Decimal(str(percentual))
            valor = _q2(valor_base * perc / Decimal("100"))
            self.db.add(
                Comissao(
                    profissional_id=profissional_id,
                    conta_receber_id=conta.id,
                    contrato_id=conta.contrato_id,
                    competencia=inicio,
                    valor_base=valor_base,
                    percentual=perc,
                    valor=valor,
                    status=ComissaoStatus.pendente,
                )
            )
            geradas += 1
            total += valor
            ja_geradas.add(conta.id)

        self.db.commit()
        return {"competencia": competencia, "geradas": geradas, "valor_total": float(total)}

    def listar(self, profissional_id: int | None, competencia: str | None, status_filtro: str | None):
        stmt = select(Comissao)
        if profissional_id is not None:
            stmt = stmt.where(Comissao.profissional_id == profissional_id)
        if competencia:
            inicio, _ = parse_competencia(competencia)
            stmt = stmt.where(Comissao.competencia == inicio)
        if status_filtro:
            stmt = stmt.where(Comissao.status == status_filtro)
        stmt = stmt.order_by(Comissao.competencia.desc(), Comissao.id.desc())
        return self.db.execute(stmt).scalars().all()

    def resumo(self, profissional_id: int | None, competencia: str | None) -> dict:
        filtros = []
        if profissional_id is not None:
            filtros.append(Comissao.profissional_id == profissional_id)
        if competencia:
            inicio, _ = parse_competencia(competencia)
            filtros.append(Comissao.competencia == inicio)

        pendente = func.coalesce(
            func.sum(case((Comissao.status == ComissaoStatus.pendente.value, Comissao.valor), else_=0)), 0
        )
        pago = func.coalesce(
            func.sum(case((Comissao.status == ComissaoStatus.pago.value, Comissao.valor), else_=0)), 0
        )
        stmt = (
            select(
                Comissao.profissional_id,
                Profissional.nome,
                func.count(Comissao.id),
                pendente,
                pago,
            )
            .join(Profissional, Comissao.profissional_id == Profissional.id)
            .group_by(Comissao.profissional_id, Profissional.nome)
            .order_by(Profissional.nome.asc())
        )
        for f in filtros:
            stmt = stmt.where(f)

        itens = []
        total = Decimal("0.00")
        for prof_id, nome, qtd, val_pendente, val_pago in self.db.execute(stmt).all():
            vp = _q2(val_pendente)
            vg = _q2(val_pago)
            vt = vp + vg
            total += vt
            itens.append(
                {
                    "profissional_id": prof_id,
                    "profissional_nome": nome,
                    "competencia": competencia,
                    "quantidade": qtd,
                    "valor_pendente": float(vp),
                    "valor_pago": float(vg),
                    "valor_total": float(vt),
                }
            )
        return {"competencia": competencia, "itens": itens, "valor_total": float(total)}

    def get_or_404(self, comissao_id: int) -> Comissao:
        c = self.db.get(Comissao, comissao_id)
        if not c:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comissao not found")
        return c

    def pagar(self, comissao_id: int, pago_em: date | None) -> Comissao:
        c = self.get_or_404(comissao_id)
        c.status = ComissaoStatus.pago
        c.pago_em = pago_em or date.today()
        self.db.commit()
        self.db.refresh(c)
        return c
