from pathlib import Path
import sys

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))

from amazon_sales_analysis.analytics import add_derived_metrics, summarize_kpis

ASSETS_CSS = ROOT_DIR / "assets" / "custom.css"
DATASET_PATH = ROOT_DIR / "data" / "processed" / "amazon_sales_clean.csv"
LOGO_LOCAL_PATH = ROOT_DIR / "assets" / "amazon_logo.svg"
LOGO_FALLBACK_URL = "https://upload.wikimedia.org/wikipedia/commons/a/a9/Amazon_logo.svg"

st.set_page_config(
    page_title="Amazon Sales Analytics",
    page_icon="A",
    layout="wide",
    initial_sidebar_state="expanded",
)

if ASSETS_CSS.exists():
    st.markdown(f"<style>{ASSETS_CSS.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


@st.cache_data(ttl=3600)
def load_processed_data() -> pd.DataFrame:
    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            "Dataset processado nao encontrado. Execute: python scripts/run_pipeline.py"
        )
    frame = pd.read_csv(DATASET_PATH, parse_dates=["order_date"])
    return add_derived_metrics(frame)


def render_logo() -> None:
    if LOGO_LOCAL_PATH.exists():
        st.image(str(LOGO_LOCAL_PATH), width=190)
        return
    st.image(LOGO_FALLBACK_URL, width=190)


def render_header() -> None:
    st.markdown('<h1 class="main-header">Amazon Sales Analytics</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">Portfolio de dados com foco executivo: pipeline reproduzivel, qualidade e impacto de negocio.</p>',
        unsafe_allow_html=True,
    )


def render_sidebar(df: pd.DataFrame) -> pd.DataFrame:
    with st.sidebar:
        render_logo()
        st.markdown("### Decision Controls")

        start_default = df["order_date"].min().date()
        end_default = df["order_date"].max().date()
        date_range = st.date_input(
            "Periodo",
            value=(start_default, end_default),
            min_value=start_default,
            max_value=end_default,
        )
        if len(date_range) == 2:
            start_date, end_date = date_range
        else:
            start_date = end_date = start_default

        regions = ["All"] + sorted(df["customer_region"].dropna().unique().tolist())
        categories = ["All"] + sorted(df["product_category"].dropna().unique().tolist())
        payment_methods = ["All"] + sorted(df["payment_method"].dropna().unique().tolist())

        selected_region = st.selectbox("Regiao", regions)
        selected_category = st.selectbox("Categoria", categories)
        selected_payment = st.selectbox("Pagamento", payment_methods)

        st.markdown("---")
        st.caption(f"Range: {start_date} ate {end_date}")

    filtered = df[(df["order_date"].dt.date >= start_date) & (df["order_date"].dt.date <= end_date)]
    if selected_region != "All":
        filtered = filtered[filtered["customer_region"] == selected_region]
    if selected_category != "All":
        filtered = filtered[filtered["product_category"] == selected_category]
    if selected_payment != "All":
        filtered = filtered[filtered["payment_method"] == selected_payment]

    return filtered


def render_kpis(df_filtered: pd.DataFrame, df_all: pd.DataFrame) -> None:
    kpis = summarize_kpis(df_filtered)
    baseline = summarize_kpis(df_all)

    coverage = (kpis["total_revenue"] / baseline["total_revenue"] * 100) if baseline["total_revenue"] else 0
    order_share = (kpis["total_orders"] / baseline["total_orders"] * 100) if baseline["total_orders"] else 0

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Receita Total", f"${kpis['total_revenue']:,.0f}", f"{coverage:.1f}% do total")
    col2.metric("Pedidos", f"{kpis['total_orders']:,.0f}", f"{order_share:.1f}% do total")
    col3.metric("Unidades", f"{kpis['total_units']:,.0f}")
    col4.metric("Ticket Medio", f"${kpis['avg_ticket']:,.2f}")
    col5.metric("Rating Medio", f"{kpis['avg_rating']:.2f}")
    col6.metric("North Star NRR", f"{kpis['net_revenue_retained'] * 100:.2f}%")


def render_exec_dashboard(df: pd.DataFrame) -> None:
    if df.empty:
        st.warning("Sem dados para o recorte selecionado.")
        return

    col1, col2 = st.columns(2)

    region_revenue = df.groupby("customer_region", as_index=False)["total_revenue"].sum()
    payment_revenue = df.groupby("payment_method", as_index=False)["total_revenue"].sum()

    with col1:
        fig = px.pie(
            region_revenue,
            values="total_revenue",
            names="customer_region",
            title="Receita por Regiao",
            hole=0.48,
        )
        fig.update_layout(margin=dict(l=10, r=10, t=50, b=10))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.bar(
            payment_revenue,
            x="payment_method",
            y="total_revenue",
            title="Receita por Metodo de Pagamento",
            color="total_revenue",
            color_continuous_scale="blues",
        )
        fig.update_layout(margin=dict(l=10, r=10, t=50, b=10), coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    monthly = (
        df.groupby(pd.Grouper(key="order_date", freq="ME"), as_index=False)["total_revenue"]
        .sum()
        .sort_values("order_date")
    )
    trend = px.line(
        monthly,
        x="order_date",
        y="total_revenue",
        markers=True,
        title="Tendencia Mensal de Receita",
    )
    trend.update_layout(margin=dict(l=10, r=10, t=50, b=10))
    st.plotly_chart(trend, use_container_width=True)


def render_recruiter_section(df: pd.DataFrame) -> None:
    st.subheader("Sinais de Senioridade Tecnica")
    st.markdown(
        """
- Arquitetura orientada a dominio (`src/amazon_sales_analysis`) com separacao clara de responsabilidades.
- Pipeline executavel por script, com fallback para ambiente sem `kagglehub`.
- Padrao de qualidade com testes automatizados para regras de limpeza e dominio.
- Dashboard orientado a decisao: KPI, segmentacao, tendencia e leitura executiva.
        """
    )

    top_categories = (
        df.groupby("product_category", as_index=False)["total_revenue"]
        .sum()
        .sort_values("total_revenue", ascending=False)
        .head(10)
    )
    fig = px.bar(
        top_categories,
        x="total_revenue",
        y="product_category",
        orientation="h",
        title="Top 10 Categorias por Receita",
        color="total_revenue",
        color_continuous_scale="oranges",
    )
    fig.update_layout(margin=dict(l=10, r=10, t=50, b=10), coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)


def render_data_quality(df: pd.DataFrame) -> None:
    summary = pd.DataFrame(
        {
            "Indicador": [
                "Total de linhas",
                "Nulos totais",
                "Pedidos duplicados",
                "Discount fora de 0-100",
                "Rating fora de 0-5",
            ],
            "Valor": [
                len(df),
                int(df.isna().sum().sum()),
                int(df["order_id"].duplicated().sum()),
                int(((df["discount_percent"] < 0) | (df["discount_percent"] > 100)).sum()),
                int(((df["rating"] < 0) | (df["rating"] > 5)).sum()),
            ],
        }
    )
    st.dataframe(summary, use_container_width=True, hide_index=True)


def main() -> None:
    render_header()

    try:
        df_all = load_processed_data()
    except Exception as exc:
        st.error(str(exc))
        st.stop()

    filtered_df = render_sidebar(df_all)
    if filtered_df.empty:
        st.warning("Nenhum registro encontrado para os filtros selecionados.")
        return

    render_kpis(filtered_df, df_all)

    tab1, tab2, tab3 = st.tabs(
        ["Dashboard Executivo", "Perfil para Recrutadores", "Qualidade dos Dados"]
    )
    with tab1:
        render_exec_dashboard(filtered_df)
    with tab2:
        render_recruiter_section(filtered_df)
    with tab3:
        render_data_quality(filtered_df)


if __name__ == "__main__":
    main()
