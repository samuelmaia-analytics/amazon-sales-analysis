from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, cast

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from amazon_sales_analysis.config import PROCESSED_DATA_DIR, get_settings
from amazon_sales_analysis.decision_engine import build_actionable_recommendations
from amazon_sales_analysis.insights import generate_executive_insights
from amazon_sales_analysis.modeling import rank_discount_opportunities
from amazon_sales_analysis.sales_analysis import build_executive_report, prepare_sales_frame
from amazon_sales_analysis.serving.operations import latest_operational_summary
from amazon_sales_analysis.serving.run_history import compare_latest_runs, summarize_run_history
from amazon_sales_analysis.transformations.data_preprocessing import read_sales_dataset
from amazon_sales_analysis.validation.quality import summarize_quality_gates
from amazon_sales_analysis.warehouse_service import warehouse_query_metadata

ROOT_DIR = PROJECT_ROOT
DATASET_PATH = PROCESSED_DATA_DIR / "amazon_sales_clean.csv"
CUSTOM_CSS_PATH = ROOT_DIR / "assets" / "custom.css"

st.set_page_config(page_title="Amazon Sales Executive Cockpit", layout="wide")


@st.cache_data(ttl=3600)
def load_dataset(path: Path) -> pd.DataFrame:
    frame = read_sales_dataset(path)
    return cast(pd.DataFrame, prepare_sales_frame(frame))


@st.cache_data(ttl=300)
def load_operational_summary() -> dict[str, object] | None:
    try:
        return cast(dict[str, object], latest_operational_summary())
    except FileNotFoundError:
        return None


@st.cache_data(ttl=300)
def load_run_history() -> list[dict[str, object]]:
    return cast(list[dict[str, object]], summarize_run_history(limit=8))


@st.cache_data(ttl=300)
def load_run_comparison() -> dict[str, object] | None:
    try:
        return cast(dict[str, object], compare_latest_runs())
    except ValueError:
        return None


@st.cache_data(ttl=300)
def load_warehouse_metadata() -> dict[str, object]:
    return cast(dict[str, object], warehouse_query_metadata())


def load_custom_css() -> None:
    if CUSTOM_CSS_PATH.exists():
        st.markdown(
            f"<style>{CUSTOM_CSS_PATH.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True
        )


def format_currency(value: float) -> str:
    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    if abs(value) >= 1_000:
        return f"${value / 1_000:.1f}K"
    return f"${value:,.0f}"


def format_delta_currency(value: float) -> str:
    signal = "+" if value >= 0 else "-"
    return f"{signal}{format_currency(abs(value))}"


def format_delta_percent(value: float) -> str:
    return f"{value:+.1f}%"


def format_percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def _as_mapping(value: object) -> dict[str, Any]:
    return cast(dict[str, Any], value if isinstance(value, dict) else {})


def _apply_exec_chart_style(fig: go.Figure, *, yaxis_title: str = "", xaxis_title: str = "") -> go.Figure:
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="white",
        plot_bgcolor="white",
        font={"family": "Inter, Segoe UI, Arial, sans-serif", "size": 14, "color": "#111827"},
        colorway=["#0f766e", "#1f8f5f", "#334155", "#be123c", "#0ea5e9"],
        title={"font": {"size": 20, "color": "#0f172a"}},
        margin={"l": 16, "r": 16, "t": 56, "b": 16},
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1.0,
        },
    )
    fig.update_xaxes(
        title_text=xaxis_title,
        showgrid=True,
        gridcolor="#e5e7eb",
        tickfont={"color": "#334155", "size": 12},
        title_font={"color": "#334155", "size": 13},
    )
    fig.update_yaxes(
        title_text=yaxis_title,
        showgrid=True,
        gridcolor="#e5e7eb",
        tickfont={"color": "#334155", "size": 12},
        title_font={"color": "#334155", "size": 13},
    )
    fig.update_layout(
        coloraxis_colorbar={
            "title": {"font": {"size": 12, "color": "#334155"}},
            "tickfont": {"size": 12, "color": "#334155"},
        }
    )
    return fig


def _monthly_summary(df: pd.DataFrame) -> pd.DataFrame:
    monthly = (
        df.groupby("month_start", as_index=False)
        .agg(
            total_revenue=("total_revenue", "sum"),
            gross_revenue=("gross_revenue", "sum"),
            orders=("order_id", "nunique"),
            discount_value=("discount_value", "sum"),
        )
        .sort_values("month_start")
    )
    monthly["avg_order_value"] = monthly["total_revenue"] / monthly["orders"].replace(0, pd.NA)
    monthly["nrr"] = monthly["total_revenue"] / monthly["gross_revenue"].replace(0, pd.NA)
    return monthly.fillna(0.0)


def _business_filtered_frame(df: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.header("Escopo Executivo")

    categories = sorted(df["product_category"].dropna().astype(str).unique())
    selected_categories = st.sidebar.multiselect(
        "Categorias",
        options=categories,
        default=categories,
    )

    min_date = pd.to_datetime(df["order_date"], errors="coerce").min()
    max_date = pd.to_datetime(df["order_date"], errors="coerce").max()
    default_dates = (min_date.date(), max_date.date()) if pd.notna(min_date) and pd.notna(max_date) else None
    date_range = st.sidebar.date_input("Período", value=default_dates)

    filtered = df.copy()
    if selected_categories:
        filtered = filtered[filtered["product_category"].astype(str).isin(selected_categories)]

    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
        filtered = filtered[
            (pd.to_datetime(filtered["order_date"], errors="coerce").dt.date >= start_date)
            & (pd.to_datetime(filtered["order_date"], errors="coerce").dt.date <= end_date)
        ]

    st.sidebar.caption(f"Linhas ativas: {len(filtered):,}")
    st.sidebar.caption(f"Categorias ativas: {filtered['product_category'].nunique():,}")
    if st.sidebar.button("Atualizar dados", type="primary"):
        st.cache_data.clear()
        st.rerun()

    return filtered


def _kpi_block(df: pd.DataFrame) -> None:
    monthly = _monthly_summary(df)
    if monthly.empty:
        st.warning("Sem dados para o período selecionado.")
        return

    current = monthly.iloc[-1]
    previous = monthly.iloc[-2] if len(monthly) > 1 else None

    def delta(current_value: float, previous_value: float | None) -> float:
        if previous_value is None:
            return 0.0
        return float(current_value - previous_value)

    revenue_delta = delta(float(current["total_revenue"]), None if previous is None else float(previous["total_revenue"]))
    aov_delta = delta(float(current["avg_order_value"]), None if previous is None else float(previous["avg_order_value"]))
    nrr_delta_pct = (
        0.0
        if previous is None or float(previous["nrr"]) == 0
        else ((float(current["nrr"]) - float(previous["nrr"])) / float(previous["nrr"])) * 100
    )
    leakage_delta = delta(float(current["discount_value"]), None if previous is None else float(previous["discount_value"]))

    def _metric_card(title: str, value: str, delta_text: str, is_positive_good: bool = True) -> str:
        is_positive = delta_text.strip().startswith("+")
        if is_positive_good:
            delta_class = "delta-positive" if is_positive else "delta-negative"
        else:
            delta_class = "delta-negative" if is_positive else "delta-positive"
        return (
            "<div class='kpi-card'>"
            f"<div class='kpi-title'>{title}</div>"
            f"<div class='kpi-value'>{value}</div>"
            f"<div class='kpi-delta {delta_class}'>{delta_text} vs mês anterior</div>"
            "</div>"
        )

    col1, col2, col3, col4 = st.columns(4)
    col1.markdown(
        _metric_card(
            "Receita",
            format_currency(float(current["total_revenue"])),
            format_delta_currency(revenue_delta),
            is_positive_good=True,
        ),
        unsafe_allow_html=True,
    )
    col2.markdown(
        _metric_card(
            "Ticket Médio",
            format_currency(float(current["avg_order_value"])),
            format_delta_currency(aov_delta),
            is_positive_good=True,
        ),
        unsafe_allow_html=True,
    )
    col3.markdown(
        _metric_card(
            "NRR",
            f"{float(current['nrr']) * 100:.1f}%",
            format_delta_percent(nrr_delta_pct),
            is_positive_good=True,
        ),
        unsafe_allow_html=True,
    )
    col4.markdown(
        _metric_card(
            "Discount Leakage",
            format_currency(float(current["discount_value"])),
            format_delta_currency(leakage_delta),
            is_positive_good=False,
        ),
        unsafe_allow_html=True,
    )


def _executive_tab(df: pd.DataFrame) -> None:
    insights = generate_executive_insights(df)
    report = build_executive_report(df, insights)
    recommendations = build_actionable_recommendations(df)
    monthly = _monthly_summary(df)

    st.subheader("Resumo de Decisão")
    st.dataframe(report.insights, width="stretch", hide_index=True)

    upper_left, upper_right = st.columns([1.35, 1], gap="large")
    with upper_left:
        trend = px.line(
            monthly,
            x="month_start",
            y=["total_revenue", "gross_revenue"],
            title="Receita líquida vs receita bruta por mês",
            markers=True,
        )
        trend.update_traces(line={"width": 3})
        trend.update_yaxes(tickprefix="$", separatethousands=True)
        _apply_exec_chart_style(trend, xaxis_title="Mês", yaxis_title="Receita (USD)")
        st.plotly_chart(trend, width="stretch")

    with upper_right:
        top_categories = report.category_performance.head(8).copy()
        top_categories = top_categories.sort_values("revenue", ascending=True)
        top_categories["revenue_label"] = top_categories["revenue"].map(format_currency)
        category_chart = px.bar(
            top_categories,
            x="revenue",
            y="product_category",
            orientation="h",
            title="Top categorias por receita",
            text="revenue_label",
            color="discount_pressure",
            color_continuous_scale="YlGnBu",
        )
        category_chart.update_traces(textposition="outside")
        category_chart.update_xaxes(tickprefix="$", separatethousands=True)
        _apply_exec_chart_style(category_chart, xaxis_title="Receita (USD)", yaxis_title="Categoria")
        st.plotly_chart(category_chart, width="stretch")

    st.subheader("Ações Recomendadas")
    recommendations = recommendations.copy()
    recommendations["expected_impact_usd"] = recommendations["expected_impact_usd"].map(
        lambda v: format_currency(float(v))
    )
    st.dataframe(recommendations, width="stretch", hide_index=True)


def _risk_tab(df: pd.DataFrame) -> None:
    st.subheader("Riscos e Oportunidades")

    opportunities = rank_discount_opportunities(df, top_n=10)
    opportunities = opportunities.sort_values("discount_to_revenue_ratio", ascending=False)

    left, right = st.columns([1, 1], gap="large")
    with left:
        risk_chart = px.bar(
            opportunities,
            x="discount_to_revenue_ratio",
            y="product_category",
            orientation="h",
            title="Pressão de desconto / receita por categoria",
            text=opportunities["discount_to_revenue_ratio"].map(lambda v: f"{v:.1%}"),
            color="discount_value",
            color_continuous_scale="OrRd",
        )
        risk_chart.update_traces(textposition="outside", cliponaxis=False)
        risk_chart.update_xaxes(tickformat=".0%")
        _apply_exec_chart_style(
            risk_chart,
            xaxis_title="Razão desconto / receita",
            yaxis_title="Categoria",
        )
        st.plotly_chart(risk_chart, width="stretch")

    with right:
        product_mix = (
        df.groupby("product_category", as_index=False)
        .agg(
            revenue=("total_revenue", "sum"),
            orders=("order_id", "nunique"),
            avg_discount=("discount_percent", "mean"),
        )
        .sort_values("revenue", ascending=False)
        )
        bubble = px.scatter(
            product_mix,
            x="avg_discount",
            y="revenue",
            size="orders",
            title="Mapa de categorias: desconto médio x receita",
            color_discrete_sequence=["#0f766e"],
            hover_name="product_category",
        )
        bubble.update_xaxes(ticksuffix="%")
        bubble.update_yaxes(tickprefix="$", separatethousands=True)
        _apply_exec_chart_style(
            bubble,
            xaxis_title="Desconto médio (%)",
            yaxis_title="Receita (USD)",
        )
        st.plotly_chart(bubble, width="stretch")

    opportunities_display = opportunities.copy()
    opportunities_display["discount_to_revenue_ratio"] = opportunities_display[
        "discount_to_revenue_ratio"
    ].map(lambda v: f"{float(v):.1%}")
    opportunities_display["total_revenue"] = opportunities_display["total_revenue"].map(
        lambda v: format_currency(float(v))
    )
    opportunities_display["discount_value"] = opportunities_display["discount_value"].map(
        lambda v: format_currency(float(v))
    )
    st.dataframe(opportunities_display, width="stretch", hide_index=True)


def _operations_tab(df: pd.DataFrame) -> None:
    operational_summary = load_operational_summary()
    run_history = load_run_history()
    run_comparison = load_run_comparison()
    warehouse_metadata = load_warehouse_metadata()
    settings = get_settings()

    st.subheader("Saúde Operacional do Produto de Dados")
    if operational_summary is None:
        st.warning("Nenhum run operacional encontrado.")
        st.caption(
            "Execute: amazon-sales-pipeline --retention-runs 60 para gerar histórico operacional."
        )
    else:
        run_status = _as_mapping(operational_summary.get("run_status", {}))
        quality = _as_mapping(operational_summary.get("quality_gates", {}))
        regression = _as_mapping(operational_summary.get("metrics_regression", {}))
        warehouse = _as_mapping(operational_summary.get("warehouse_validation", {}))

        status_cols = st.columns(4)
        status_cols[0].metric("Run Status", str(run_status.get("status", "unknown")))
        status_cols[1].metric("Quality Gates", str(quality.get("status", "unknown")))
        status_cols[2].metric("KPI Regression", str(regression.get("status", "unknown")))
        status_cols[3].metric("Warehouse", str(warehouse.get("status", "unknown")))

        st.caption(
            f"run_id={operational_summary.get('run_id', 'n/a')} | "
            f"pipeline_version={operational_summary.get('pipeline_version', 'n/a')} | "
            f"environment={settings.environment}"
        )

    left, right = st.columns([1.25, 1], gap="large")
    latest_run = run_history[0] if run_history else None
    latest_successful_run = next(
        (run for run in run_history if str(run.get("status", "")).lower() == "succeeded"),
        None,
    )

    run_cols = st.columns(2)
    with run_cols[0]:
        if latest_run is None:
            st.info("Último run: indisponível")
        else:
            st.markdown(
                
                    "**Último run**  \n"
                    f"run_id: `{latest_run.get('run_id', '')}`  \n"
                    f"status: `{latest_run.get('status', '')}`  \n"
                    f"início: `{latest_run.get('started_at_utc', '')}`"
                
            )
    with run_cols[1]:
        if latest_successful_run is None:
            st.warning("Último run bem-sucedido: não encontrado")
        else:
            st.markdown(
                
                    "**Último run bem-sucedido**  \n"
                    f"run_id: `{latest_successful_run.get('run_id', '')}`  \n"
                    f"status: `{latest_successful_run.get('status', '')}`  \n"
                    f"início: `{latest_successful_run.get('started_at_utc', '')}`"
                
            )

    with left:
        st.markdown("**Histórico recente de runs**")
        if run_history:
            history = pd.DataFrame(run_history).copy()
            if "total_revenue" in history.columns:
                history["total_revenue"] = history["total_revenue"].map(lambda v: format_currency(float(v)))
            if "avg_ticket" in history.columns:
                history["avg_ticket"] = history["avg_ticket"].map(lambda v: format_currency(float(v)))
            st.dataframe(history, width="stretch", hide_index=True)
        else:
            st.info("Sem histórico disponível.")

    with right:
        st.markdown("**Drift dos últimos runs**")
        if run_comparison is None:
            st.info("São necessários ao menos dois runs para comparação.")
        else:
            st.metric("Severidade geral", str(run_comparison.get("overall_severity", "unknown")))
            drift_df = (
                pd.DataFrame(cast(dict[str, Any], run_comparison["kpi_deltas"]))
                .T.reset_index()
                .rename(columns={"index": "metric"})
                .sort_values("delta_ratio", ascending=False)
            )
            drift_df["delta_ratio"] = drift_df["delta_ratio"].map(lambda v: format_percent(float(v)))
            st.dataframe(drift_df, width="stretch", hide_index=True)

    st.markdown("**Validação de qualidade sobre recorte atual**")
    st.dataframe(summarize_quality_gates(df), width="stretch", hide_index=True)

    st.markdown("**Metadados de acesso analítico**")
    metadata_table = pd.DataFrame(
        [
            {"campo": "warehouse_db_path", "valor": str(warehouse_metadata.get("warehouse_db_path", ""))},
            {"campo": "warehouse_table", "valor": str(warehouse_metadata.get("warehouse_table", ""))},
            {
                "campo": "duckdb_available",
                "valor": "true" if bool(warehouse_metadata.get("duckdb_available", False)) else "false",
            },
        ]
    )
    st.dataframe(metadata_table, width="stretch", hide_index=True)


def _catalog_tab(df: pd.DataFrame) -> None:
    report = build_executive_report(df, generate_executive_insights(df))
    st.subheader("Catálogo de KPIs")
    catalog = report.kpi_catalog.copy()
    query = st.text_input("Buscar KPI (slug, nome ou pergunta de negócio)", value="")
    if query.strip():
        token = query.strip().lower()
        catalog = catalog[
            catalog.apply(
                lambda row: any(token in str(value).lower() for value in row.values),
                axis=1,
            )
        ]

    st.dataframe(
        catalog,
        width="stretch",
        hide_index=True,
        column_config={
            "slug": st.column_config.TextColumn("slug", width="medium"),
            "name": st.column_config.TextColumn("name", width="medium"),
            "description": st.column_config.TextColumn("description", width="large"),
            "business_question": st.column_config.TextColumn("business_question", width="large"),
            "formula": st.column_config.TextColumn("formula", width="large"),
        },
    )

    if not catalog.empty:
        selected_slug = st.selectbox(
            "Detalhar KPI",
            options=sorted(catalog["slug"].astype(str).tolist()),
            index=0,
        )
        selected = catalog[catalog["slug"] == selected_slug].iloc[0]
        st.markdown(
            
                f"**KPI:** {selected['name']}  \n"
                f"**Pergunta de negócio:** {selected['business_question']}  \n"
                f"**Fórmula:** `{selected['formula']}`"
            
        )


def main() -> None:
    load_custom_css()
    st.markdown("<div class='main-header'>Amazon Sales Executive Cockpit</div>", unsafe_allow_html=True)
    st.markdown(
        (
            "<div class='sub-header'>Painel executivo para decisões de receita, margem promocional "
            "e confiabilidade operacional do pipeline analítico.</div>"
        ),
        unsafe_allow_html=True,
    )

    try:
        base_df = load_dataset(DATASET_PATH)
    except Exception as exc:
        st.error(str(exc))
        st.stop()

    filtered_df = _business_filtered_frame(base_df)
    if filtered_df.empty:
        st.warning("O recorte selecionado não possui dados.")
        st.stop()

    _kpi_block(filtered_df)

    tabs = st.tabs(
        [
            "Resumo Executivo",
            "Risco e Oportunidade",
            "Saúde Operacional",
            "Catálogo de KPIs",
        ]
    )

    with tabs[0]:
        _executive_tab(filtered_df)
    with tabs[1]:
        _risk_tab(filtered_df)
    with tabs[2]:
        _operations_tab(filtered_df)
    with tabs[3]:
        _catalog_tab(filtered_df)


if __name__ == "__main__":
    main()
