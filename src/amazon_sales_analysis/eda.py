import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from .config import FIGURES_DIR


def basic_eda(df: pd.DataFrame) -> None:
    print("==== DataFrame Info ====")
    df.info()
    print("\n==== Numeric Describe ====")
    print(df.describe())

    plt.figure(figsize=(8, 5))
    sns.histplot(df["price"], kde=True)
    plt.title("Price Distribution")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "dist_price.png")
    plt.close()

    plt.figure(figsize=(10, 8))
    sns.heatmap(df.select_dtypes("number").corr(), cmap="viridis")
    plt.title("Correlation Matrix")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "correlation_matrix.png")
    plt.close()
