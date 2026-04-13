CREATE OR REPLACE VIEW vw_category_revenue AS
SELECT
    product_category,
    SUM(total_revenue) AS revenue,
    COUNT(DISTINCT order_id) AS orders,
    AVG(discount_percent) AS avg_discount_percent
FROM gold_commercial_performance
GROUP BY product_category;
