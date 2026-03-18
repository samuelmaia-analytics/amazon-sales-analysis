SELECT
    product_category,
    ROUND(SUM(total_revenue), 2) AS revenue,
    COUNT(DISTINCT order_id) AS orders,
    ROUND(AVG(discount_percent), 2) AS avg_discount_percent
FROM gold_commercial_performance
GROUP BY product_category
ORDER BY revenue DESC;
