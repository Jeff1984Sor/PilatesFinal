from app.modules.financeiro.repository import (
    FornecedorRepository, CategoriaRepository, SubcategoriaRepository,
    ContasPagarRepository, ContasReceberRepository,
)


class FinanceiroService:
    def __init__(
        self,
        fornecedor: FornecedorRepository,
        categoria: CategoriaRepository,
        subcategoria: SubcategoriaRepository,
        contas_pagar: ContasPagarRepository,
        contas_receber: ContasReceberRepository,
    ):
        self.fornecedor = fornecedor
        self.categoria = categoria
        self.subcategoria = subcategoria
        self.contas_pagar = contas_pagar
        self.contas_receber = contas_receber
