from __future__ import annotations

from dataclasses import asdict, dataclass

import pandas as pd


@dataclass(frozen=True)
class KPIDefinition:
    slug: str
    name: str
    description: str
    business_question: str
    formula: str


KPI_CATALOG = [
    KPIDefinition(
        slug="total_revenue",
        name="Revenue total",
        description="Receita liquida capturada no periodo analisado.",
        business_question="Quanto a operacao comercial gerou de receita?",
        formula="sum(total_revenue)",
    ),
    KPIDefinition(
        slug="avg_order_value",
        name="Ticket medio",
        description="Valor medio gerado por pedido.",
        business_question="Qual e o valor medio de cada pedido?",
        formula="total_revenue / unique_orders",
    ),
    KPIDefinition(
        slug="category_revenue",
        name="Vendas por categoria",
        description="Concentracao de receita por categoria para priorizacao comercial.",
        business_question="Quais categorias lideram performance e quais exigem atencao?",
        formula="sum(total_revenue) by product_category",
    ),
    KPIDefinition(
        slug="product_contribution",
        name="Contribuicao de produtos",
        description="Participacao dos produtos no revenue total.",
        business_question="Quais produtos sustentam o resultado comercial?",
        formula="product_revenue / total_revenue",
    ),
    KPIDefinition(
        slug="growth_trend",
        name="Tendencia temporal",
        description="Evolucao mensal do revenue e sua variacao.",
        business_question="A operacao esta acelerando, estavel ou desacelerando?",
        formula="monthly_revenue and monthly_growth_rate",
    ),
    KPIDefinition(
        slug="performance_distribution",
        name="Distribuicao de performance",
        description="Perfil de dispersao do revenue por pedido para diagnostico de concentracao.",
        business_question="A performance esta pulverizada ou concentrada em poucos pedidos?",
        formula="describe(total_revenue by order)",
    ),
]


def build_kpi_catalog() -> pd.DataFrame:
    return pd.DataFrame(asdict(item) for item in KPI_CATALOG)
