from __future__ import annotations

import pandas as pd

from .sales_analysis import (
    analyze_category_performance,
    analyze_growth_trends,
    analyze_product_contribution,
    prepare_sales_frame,
)


def generate_executive_insights(df: pd.DataFrame) -> pd.DataFrame:
    prepared = prepare_sales_frame(df)
    category = analyze_category_performance(prepared)
    products = analyze_product_contribution(prepared, top_n=3)
    growth = analyze_growth_trends(prepared)

    total_revenue = float(prepared["total_revenue"].sum()) if not prepared.empty else 0.0
    avg_ticket = (
        total_revenue / float(prepared["order_id"].nunique()) if not prepared.empty else 0.0
    )

    insights: list[dict[str, str | float]] = [
        {
            "priority": "high",
            "headline": "Revenue baseline consolidada",
            "insight": (
                f"O periodo analisado gerou {total_revenue:,.2f} em revenue com ticket medio "
                f"de {avg_ticket:,.2f}."
            ),
        }
    ]

    if not category.empty:
        top_category = category.iloc[0]
        insights.append(
            {
                "priority": "high",
                "headline": "Categoria lidera o resultado",
                "insight": (
                    f"{top_category['product_category']} responde por "
                    f"{float(top_category['revenue_share']) * 100:.1f}% do revenue e deve ser "
                    "tratada como frente prioritaria de monitoramento comercial."
                ),
            }
        )

        highest_pressure = category.sort_values("discount_pressure", ascending=False).iloc[0]
        insights.append(
            {
                "priority": "medium",
                "headline": "Pressao promocional identificada",
                "insight": (
                    f"{highest_pressure['product_category']} combina maior pressao de desconto "
                    f"({float(highest_pressure['discount_pressure']) * 100:.1f}%) com impacto "
                    "relevante no revenue, indicando oportunidade de revisar politica comercial."
                ),
            }
        )

    if not products.empty:
        lead_product = products.iloc[0]
        insights.append(
            {
                "priority": "medium",
                "headline": "Concentracao em produto lider",
                "insight": (
                    f"O produto {int(lead_product['product_id'])} e o maior contribuinte individual, "
                    f"com {float(lead_product['revenue_share']) * 100:.1f}% do revenue total."
                ),
            }
        )

    if not growth.empty:
        latest = growth.iloc[-1]
        insights.append(
            {
                "priority": "high",
                "headline": "Tendencia temporal",
                "insight": (
                    f"O ultimo mes encerrou em {latest['momentum'].lower()} com variacao de "
                    f"{float(latest['revenue_growth_rate']) * 100:.1f}% no revenue mensal."
                ),
            }
        )

    return pd.DataFrame(insights)
