-- Athena SQL queries for the sample-domain curated data

-- View: Daily revenue summary
CREATE OR REPLACE VIEW daily_revenue AS
SELECT
    order_date,
    category,
    region,
    order_count,
    total_revenue,
    avg_order_value,
    unique_customers,
    cumulative_revenue
FROM data_platform_dev.sales_summary
ORDER BY order_date DESC;

-- View: Monthly category performance
CREATE OR REPLACE VIEW monthly_category_performance AS
SELECT
    year,
    month,
    category,
    SUM(order_count) AS total_orders,
    SUM(total_revenue) AS monthly_revenue,
    SUM(total_quantity) AS monthly_quantity,
    AVG(avg_order_value) AS avg_order_value,
    SUM(unique_customers) AS total_customers
FROM data_platform_dev.sales_summary
GROUP BY year, month, category
ORDER BY year, month, category;

-- View: Regional performance
CREATE OR REPLACE VIEW regional_performance AS
SELECT
    region,
    year,
    month,
    SUM(total_revenue) AS revenue,
    SUM(order_count) AS orders,
    SUM(unique_customers) AS customers,
    ROUND(SUM(total_revenue) / SUM(order_count), 2) AS revenue_per_order
FROM data_platform_dev.sales_summary
GROUP BY region, year, month
ORDER BY region, year, month;

-- View: Top categories by revenue
CREATE OR REPLACE VIEW top_categories AS
SELECT
    category,
    SUM(total_revenue) AS total_revenue,
    SUM(order_count) AS total_orders,
    SUM(unique_customers) AS total_customers,
    ROUND(SUM(total_revenue) / SUM(order_count), 2) AS avg_revenue_per_order
FROM data_platform_dev.sales_summary
GROUP BY category
ORDER BY total_revenue DESC;
