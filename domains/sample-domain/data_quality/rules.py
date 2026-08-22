"""
Data Quality Rules - Định nghĩa tiêu chuẩn chất lượng dữ liệu cho sample-domain.

Sử dụng DQDL (Data Quality Definition Language) của AWS Glue.
Glue Data Quality sẽ chạy các rules này SAU mỗi lần Stage A/B transform xong.
Nếu bất kỳ rule nào FAIL, EventBridge bắt event và trigger alert Lambda.

Rules kiểm tra:
- Schema: Các cột bắt buộc phải tồn tại
- Completeness: Cột quan trọng không được null (>= 95%)
- Uniqueness: Primary key không trùng lặp
- Range: Giá trị nằm trong khoảng hợp lý (amount > 0, quantity 1-10000)
- Domain: Giá trị thuộc tập hợp cho phép (category, region, payment_method)
"""

ORDERS_STAGING_RULES = """
Rules = [
    ColumnExists "order_id",
    ColumnExists "order_date",
    ColumnExists "customer_id",
    ColumnExists "category",
    ColumnExists "total_amount",
    IsComplete "order_id",
    IsComplete "order_date",
    IsComplete "customer_id",
    IsUnique "order_id",
    ColumnValues "total_amount" > 0,
    ColumnValues "quantity" between 1 and 10000,
    ColumnValues "category" in ["Electronics", "Clothing", "Home & Garden", "Sports", "Books"],
    ColumnValues "region" in ["us-east", "us-west", "eu-west", "ap-southeast"],
    ColumnValues "payment_method" in ["credit_card", "debit_card", "paypal", "bank_transfer"],
    RowCount > 0,
    Completeness "total_amount" >= 0.95,
    Completeness "category" >= 0.99
]
"""

SALES_SUMMARY_RULES = """
Rules = [
    ColumnExists "order_date",
    ColumnExists "category",
    ColumnExists "region",
    ColumnExists "total_revenue",
    ColumnExists "order_count",
    IsComplete "order_date",
    IsComplete "category",
    IsComplete "region",
    ColumnValues "order_count" > 0,
    ColumnValues "total_revenue" > 0,
    ColumnValues "avg_order_value" > 0,
    ColumnValues "unique_customers" > 0,
    RowCount > 0
]
"""
