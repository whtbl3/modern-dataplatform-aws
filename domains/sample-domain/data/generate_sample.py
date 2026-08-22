"""
Sample Data Generator - Tạo dữ liệu e-commerce giả để test pipeline.

Tạo file orders.csv với 1000 đơn hàng ngẫu nhiên gồm:
order_id, order_date, customer_id, category, product_name,
quantity, unit_price, total_amount, region, payment_method.

Dùng để:
- Test pipeline end-to-end local (upload CSV vào S3 raw, xem pipeline chạy)
- Validate data quality rules (dữ liệu đúng format, đúng range)
- Demo cho stakeholders trước khi dùng dữ liệu thật

Chạy: uv run python domains/sample-domain/data/generate_sample.py
"""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

CATEGORIES = ["Electronics", "Clothing", "Home & Garden", "Sports", "Books"]
REGIONS = ["us-east", "us-west", "eu-west", "ap-southeast"]
PAYMENT_METHODS = ["credit_card", "debit_card", "paypal", "bank_transfer"]

OUTPUT_DIR = Path(__file__).parent


def generate_orders(num_records: int = 1000) -> list[dict]:
    """Tạo danh sách orders ngẫu nhiên trong khoảng 1 năm (2024)."""
    start_date = date(2024, 1, 1)
    records = []

    for i in range(1, num_records + 1):
        order_date = start_date + timedelta(days=random.randint(0, 365))
        category = random.choice(CATEGORIES)
        quantity = random.randint(1, 10)
        unit_price = round(random.uniform(5.0, 500.0), 2)

        records.append({
            "order_id": f"ORD-{i:06d}",
            "order_date": order_date.isoformat(),
            "customer_id": f"CUST-{random.randint(1, 200):05d}",
            "category": category,
            "product_name": f"{category}_Product_{random.randint(1, 50)}",
            "quantity": quantity,
            "unit_price": unit_price,
            "total_amount": round(quantity * unit_price, 2),
            "region": random.choice(REGIONS),
            "payment_method": random.choice(PAYMENT_METHODS),
        })

    return records


def write_csv(records: list[dict], filename: str = "orders.csv"):
    """Ghi danh sách records ra file CSV (sẵn sàng upload lên S3)."""
    filepath = OUTPUT_DIR / filename
    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)
    print(f"Generated {len(records)} records -> {filepath}")


if __name__ == "__main__":
    orders = generate_orders(1000)
    write_csv(orders)
