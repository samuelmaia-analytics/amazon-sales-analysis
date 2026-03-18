from pathlib import Path
from typing import Any, cast

import pandas as pd
import plotly.express as px
import streamlit as st

from amazon_sales_analysis.config import PROCESSED_DATA_DIR, get_settings
from amazon_sales_analysis.insights import generate_executive_insights
from amazon_sales_analysis.sales_analysis import build_executive_report, prepare_sales_frame
from amazon_sales_analysis.serving.operations import latest_operational_summary
from amazon_sales_analysis.serving.run_history import compare_latest_runs, summarize_run_history
from amazon_sales_analysis.transformations.data_preprocessing import read_sales_dataset
from amazon_sales_analysis.validation.quality import summarize_quality_gates
from amazon_sales_analysis.warehouse_service import warehouse_query_metadata

ROOT_DIR = Path(__file__).resolve().parent.parent
DATASET_PATH = PROCESSED_DATA_DIR / "amazon_sales_clean.csv"
CUSTOM_CSS_PATH = ROOT_DIR / "assets" / "custom.css"

st.set_page_config(page_title="Amazon Commercial Performance Monitor", layout="wide")


@st.cache_data(ttl=3600)
def load_dataset() -> pd.DataFrame:
    frame = read_sales_dataset(DATASET_PATH)
    return prepare_sales_frame(frame)


def format_currency(value: float) -> str:
    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    if abs(value) >= 1_000:
        return f"${value / 1_000:.1f}K"
    return f"${value:,.0f}"


def format_percent(value: float) -> str:
    return f"{value * 100:.2f}%"


def _as_mapping(value: object) -> dict[str, Any]:
    return cast(dict[str, Any], value if isinstance(value, dict) else {})


def load_custom_css() -> None:
    if CUSTOM_CSS_PATH.exists():
        st.markdown(f"<style>{CUSTOM_CSS_PATH.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


@st.cache_data(ttl=300)
def load_operational_summary() -> dict[str, object] | None:
    try:
        return latest_operational_summary()
    except FileNotFoundError:
        return None


@st.cache_data(ttl=300)
def load_run_history() -> list[dict[str, object]]:
    return summarize_run_history(limit=5)


@st.cache_data(ttl=300)
def load_run_comparison() -> dict[str, object] | None:
    try:
        return compare_latest_runs()
    except ValueError:
        return None


@st.cache_data(ttl=300)
def load_warehouse_metadata() -> dict[str, object]:
    return warehouse_query_metadata()


def main() -> None:
    load_custom_css()
    st.markdown("<div class='main-header'>Amazon Commercial Performance Monitor</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='sub-header'>Monitoramento de performance comercial com foco em revenue, "
        "ticket medio, categorias, produtos lideres, tendencia temporal e saude operacional.</div>",
        unsafe_allow_html=True,
    )

    try:
        df = load_dataset()
    except Exception as exc:
        st.error(str(exc))
        st.stop()

    insights = generate_executive_insights(df)
    report = build_executive_report(df, insights)
    kpi_lookup = dict(zip(report.kpi_summary["metric"], report.kpi_summary["value"], strict=False))
    operational_summary = load_operational_summary()
    run_history = load_run_history()
    run_comparison = load_run_comparison()
    warehouse_metadata = load_warehouse_metadata()
    settings = get_settings()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Revenue total", format_currency(float(kpi_lookup["total_revenue"])))
    col2.metric("Ticket medio", format_currency(float(kpi_lookup["avg_order_value"])))
    col3.metric("Pedidos", f"{int(kpi_lookup['total_orders']):,}")
    col4.metric("NRR", f"{float(kpi_lookup['net_revenue_retained']) * 100:.1f}%")

    if operational_summary is not None:
        top_ops_cols = st.columns([1.15, 1.15, 1.15, 1.35])
        run_status = _as_mapping(operational_summary.get("run_status", {}))
        top_ops_cols[0].metric("Status do pipeline", str(run_status.get("status", "unknown")))
        top_ops_cols[1].metric(
            "Duracao ultimo run",
            f"{float(run_status.get('duration_seconds', 0.0)):.1f}s",
        )
        top_ops_cols[2].metric(
            "Status operacional",
            str(operational_summary.get("overall_status", "unknown")),
        )
        top_ops_cols[3].metric(
            "Warehouse",
            "available" if bool(warehouse_metadata.get("duckdb_available", False)) else "fallback",
        )

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "Resumo Executivo",
            "Drivers de Performance",
            "Qualidade",
            "Operacoes",
            "Catalogo de KPIs",
        ]
    )

    with tab1:
        st.subheader("Principais achados")
        st.dataframe(report.insights, use_container_width=True, hide_index=True)

        trend_fig = px.line(
            report.growth_trends,
            x="month_start",
            y="revenue",
            markers=True,
            title="Story 1: Tendencia temporal de revenue",
        )
        st.plotly_chart(trend_fig, use_container_width=True)

        category_chart_data = report.category_performance.head(8).copy()
        category_chart_data = category_chart_data.sort_values("revenue_share", ascending=True)
        category_chart_data["revenue_share_label"] = category_chart_data["revenue_share"].map(
            format_percent
        )
        top_category = category_chart_data["product_category"].iloc[-1]
        category_chart_data["category_highlight"] = category_chart_data["product_category"].eq(
            top_category
        )

        category_fig = px.bar(
            category_chart_data,
            x="revenue_share",
            y="product_category",
            orientation="h",
            title="Story 2: Categorias que sustentam o revenue",
            text="revenue_share_label",
            color="category_highlight",
            color_discrete_map={True: "#ff8c42", False: "#ffd9bf"},
            hover_data={
                "revenue_share_label": False,
                "revenue_share": ":.2%",
                "revenue": ":,.0f",
                "orders": ":,.0f",
                "units": ":,.0f",
                "avg_order_value": ":,.2f",
                "discount_pressure": ":.2%",
                "category_highlight": False,
            },
        )
        category_fig.update_traces(textposition="outside")
        category_fig.update_layout(
            showlegend=False,
            xaxis_title="Participacao no revenue",
            yaxis_title="Categoria",
            xaxis_tickformat=".0%",
        )
        st.plotly_chart(category_fig, use_container_width=True)

    with tab2:
        product_fig = px.bar(
            report.product_contribution,
            x="revenue_share",
            y=report.product_contribution["product_id"].astype(str),
            orientation="h",
            title="Story 3: Produtos com maior contribuicao",
            color="revenue",
            color_continuous_scale="Blues",
        )
        st.plotly_chart(product_fig, use_container_width=True)

        distribution_fig = px.bar(
            report.performance_distribution,
            x="performance_band",
            y="revenue_share",
            title="Story 4: Distribuicao de performance",
            color="avg_discount",
            color_continuous_scale="Teal",
        )
        st.plotly_chart(distribution_fig, use_container_width=True)

        st.dataframe(report.category_performance, use_container_width=True, hide_index=True)

    with tab3:
        st.subheader("Validacoes de entrada")
        st.dataframe(summarize_quality_gates(df), use_container_width=True, hide_index=True)

    with tab4:
        st.subheader("Saude Operacional")
        if operational_summary is None:
            st.warning("Nenhum run operacional foi encontrado ainda.")
        else:
            run_status = _as_mapping(operational_summary.get("run_status", {}))
            quality_status = _as_mapping(operational_summary.get("quality_gates", {}))
            metrics_status = _as_mapping(operational_summary.get("metrics_regression", {}))
            warehouse_status = _as_mapping(operational_summary.get("warehouse_validation", {}))

            status_cols = st.columns(3)
            status_cols[0].metric("Quality gates", str(quality_status.get("status", "unknown")))
            status_cols[1].metric("KPI regression", str(metrics_status.get("status", "unknown")))
            status_cols[2].metric("Warehouse", str(warehouse_status.get("status", "unknown")))

            st.caption(
                "Ultimo run: "
                f"{operational_summary['run_id']} | "
                f"pipeline_version={operational_summary['pipeline_version']}"
            )

            details_col, warehouse_col = st.columns([1.15, 1], gap="large")
            with details_col:
                st.markdown("**Componentes do ultimo run**")
                operational_cards = pd.DataFrame(
                    [
                        {
                            "component": "quality_gates",
                            "status": quality_status.get("status", "unknown"),
                            "details": quality_status.get("path", ""),
                        },
                        {
                            "component": "metrics_regression",
                            "status": metrics_status.get("status", "unknown"),
                            "details": ", ".join(metrics_status.get("failed_metrics", []))
                            if isinstance(metrics_status.get("failed_metrics"), list)
                            else "",
                        },
                        {
                            "component": "warehouse_validation",
                            "status": warehouse_status.get("status", "unknown"),
                            "details": warehouse_status.get(
                                "reason", warehouse_status.get("path", "")
                            ),
                        },
                    ]
                )
                st.dataframe(
                    operational_cards,
                    use_container_width=True,
                    hide_index=True,
                    height=215,
                )

            with warehouse_col:
                st.markdown("**Camada Analitica**")
                warehouse_cols = st.columns(3)
                warehouse_cols[0].metric(
                    "DuckDB disponivel",
                    "yes" if bool(warehouse_metadata.get("duckdb_available", False)) else "no",
                )
                warehouse_cols[1].metric(
                    "Tabela", str(warehouse_metadata.get("warehouse_table", "unknown"))
                )
                warehouse_cols[2].metric("Ambiente", settings.environment)
                st.caption(str(warehouse_metadata.get("warehouse_db_path", "")))

        history_col, drift_col = st.columns([1.2, 1], gap="large")
        with history_col:
            st.subheader("Historico Recente de Runs")
            if run_history:
                history_df = pd.DataFrame(run_history)
                st.dataframe(history_df, use_container_width=True, hide_index=True, height=260)
            else:
                st.info("Historico de runs ainda nao disponivel.")

        with drift_col:
            st.subheader("Drift Entre Ultimos Runs")
            if run_comparison is None:
                st.info("Sao necessarios pelo menos dois runs para comparar drift de KPIs.")
            else:
                st.metric("Severidade geral", str(run_comparison["overall_severity"]))
                drift_df = (
                    pd.DataFrame(cast(dict[str, Any], run_comparison["kpi_deltas"]))
                    .T.reset_index()
                    .rename(columns={"index": "metric"})
                )
                st.dataframe(drift_df, use_container_width=True, hide_index=True, height=260)

    with tab5:
        st.subheader("KPIs definidos")
        st.dataframe(report.kpi_catalog, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
