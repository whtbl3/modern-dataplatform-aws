"""
Data Quality Rules - Dinh nghia tieu chuan chat luong du lieu cho sample-domain.

Su dung DQDL (Data Quality Definition Language) cua AWS Glue.
Glue Data Quality se chay cac rules nay SAU moi lan Stage A/B transform xong.
Neu bat ky rule nao FAIL, EventBridge bat event va trigger alert Lambda.

Rules kiem tra:
- Schema: Cac cot bat buoc phai ton tai
- Completeness: Cot quan trong khong duoc null (>= 95%)
- Uniqueness: Primary key khong trung lap
- Range: Gia tri nam trong khoang hop ly (amount > 0, quantity 1-10000)
- Domain: Gia tri thuoc tap hop cho phep (category, region, payment_method)
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
