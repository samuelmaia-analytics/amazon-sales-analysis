import pandas as pd

from .data_preprocessing import audit_data_quality
from .insights import generate_executive_insights
from .quality import summarize_quality_gates
from .sales_analysis import build_executive_report, prepare_sales_frame


def build_executive_tables(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    prepared = prepare_sales_frame(df)
    insights = generate_executive_insights(prepared)
    report = build_executive_report(prepared, insights)

    monthly_trend = report.growth_trends.rename(columns={"month_start": "month_end"})

    return {
        "kpi_summary": report.kpi_summary,
        "category_performance": report.category_performance,
        "product_contribution": report.product_contribution,
        "monthly_trend": monthly_trend,
        "performance_distribution": report.performance_distribution,
        "insights_summary": report.insights,
        "kpi_catalog": report.kpi_catalog,
        "data_quality_audit": audit_data_quality(prepared),
        "quality_gate_summary": summarize_quality_gates(prepared),
    }
