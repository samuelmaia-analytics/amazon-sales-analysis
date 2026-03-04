import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from .config import FIGURES_DIR


def sales_trend_over_time(df: pd.DataFrame) -> None:
    frame = df.copy()
    frame["year_month"] = pd.to_datetime(frame["order_date"]).dt.to_period("M").dt.to_timestamp()
    monthly = (
        frame.groupby("year_month")["total_revenue"].sum().reset_index().sort_values("year_month")
    )

    plt.figure(figsize=(10, 5))
    sns.lineplot(data=monthly, x="year_month", y="total_revenue", marker="o")
    plt.title("Monthly Revenue Trend")
    plt.xlabel("Year-Month")
    plt.ylabel("Total Revenue")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "sales_trend_over_time.png")
    plt.close()


def top_categories_by_sales(df: pd.DataFrame, top_n: int = 10) -> None:
    grouped = (
        df.groupby("product_category")["total_revenue"]
        .sum()
        .sort_values(ascending=False)
        .head(top_n)
    )

    plt.figure(figsize=(10, 6))
    sns.barplot(x=grouped.values, y=grouped.index)
    plt.title(f"Top {top_n} Categories by Revenue")
    plt.xlabel("Total Revenue")
    plt.ylabel("Category")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "top_categories_by_sales.png")
    plt.close()
