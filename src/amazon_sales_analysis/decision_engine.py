import pandas as pd


def build_actionable_recommendations(df: pd.DataFrame) -> pd.DataFrame:
    total_revenue = float(df["total_revenue"].sum())
    gross_revenue = float(df["gross_revenue"].sum()) if "gross_revenue" in df else 0.0
    discount_leakage = gross_revenue - total_revenue if gross_revenue else 0.0
    nrr = (total_revenue / gross_revenue) if gross_revenue else 0.0

    category_leakage = (
        df.groupby("product_category", as_index=False)
        .agg(discount_value=("discount_value", "sum"), total_revenue=("total_revenue", "sum"))
        .sort_values("discount_value", ascending=False)
    )
    top_category = (
        category_leakage.iloc[0]["product_category"] if not category_leakage.empty else "N/A"
    )
    top_category_leakage = (
        float(category_leakage.iloc[0]["discount_value"]) if not category_leakage.empty else 0.0
    )

    recs: list[dict[str, str | float]] = []

    if nrr < 0.9:
        recs.append(
            {
                "priority": "high",
                "decision_rule": "NRR below 90%",
                "recommended_action": "Reduce broad discount campaigns and enforce category-level caps.",
                "expected_impact_usd": discount_leakage * 0.05,
                "owner_area": "Revenue Operations",
            }
        )

    if top_category != "N/A":
        recs.append(
            {
                "priority": "high",
                "decision_rule": f"Highest leakage category is {top_category}",
                "recommended_action": f"Run a 2-week pricing policy test in {top_category} with tighter discount thresholds.",
                "expected_impact_usd": top_category_leakage * 0.05,
                "owner_area": "Category Management",
            }
        )

    payment_perf = (
        df.groupby("payment_method", as_index=False)
        .agg(avg_ticket=("total_revenue", "mean"), total_revenue=("total_revenue", "sum"))
        .sort_values("avg_ticket")
    )
    if not payment_perf.empty:
        weakest_payment = payment_perf.iloc[0]["payment_method"]
        recs.append(
            {
                "priority": "medium",
                "decision_rule": f"Lowest average ticket on {weakest_payment}",
                "recommended_action": f"Adjust promotion mechanics for {weakest_payment} to increase ticket size.",
                "expected_impact_usd": float(total_revenue * 0.01),
                "owner_area": "Commercial Strategy",
            }
        )

    if not recs:
        recs.append(
            {
                "priority": "low",
                "decision_rule": "No material risk detected",
                "recommended_action": "Maintain current policy and continue weekly KPI monitoring.",
                "expected_impact_usd": 0.0,
                "owner_area": "Analytics",
            }
        )

    recommendations = pd.DataFrame(recs)
    return recommendations.sort_values(
        by=["priority", "expected_impact_usd"], ascending=[True, False]
    ).reset_index(drop=True)
