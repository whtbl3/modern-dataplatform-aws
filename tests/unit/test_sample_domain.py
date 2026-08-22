"""Unit tests cho logic pipeline của sample-domain."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "domains" / "sample-domain" / "data"))
from generate_sample import generate_orders


class TestDataGeneration:

    def test_generates_correct_number_of_records(self):
        records = generate_orders(100)
        assert len(records) == 100

    def test_order_id_format(self):
        records = generate_orders(10)
        for r in records:
            assert r["order_id"].startswith("ORD-")
            assert len(r["order_id"]) == 10

    def test_valid_categories(self):
        valid = {"Electronics", "Clothing", "Home & Garden", "Sports", "Books"}
        records = generate_orders(50)
        for r in records:
            assert r["category"] in valid

    def test_valid_regions(self):
        valid = {"us-east", "us-west", "eu-west", "ap-southeast"}
        records = generate_orders(50)
        for r in records:
            assert r["region"] in valid

    def test_total_amount_calculation(self):
        records = generate_orders(50)
        for r in records:
            expected = round(r["quantity"] * r["unit_price"], 2)
            assert r["total_amount"] == expected

    def test_no_negative_values(self):
        records = generate_orders(100)
        for r in records:
            assert r["quantity"] > 0
            assert r["unit_price"] > 0
            assert r["total_amount"] > 0


class TestStageALogic:

    def test_deduplication_by_order_id(self):
        records = [
            {"order_id": "ORD-001", "amount": 100},
            {"order_id": "ORD-001", "amount": 100},
            {"order_id": "ORD-002", "amount": 200},
        ]
        deduped = list({r["order_id"]: r for r in records}.values())
        assert len(deduped) == 2

    def test_null_filter(self):
        records = [
            {"order_id": "ORD-001", "amount": 100},
            {"order_id": None, "amount": None},
            {"order_id": "ORD-003", "amount": 300},
        ]
        filtered = [r for r in records if r["order_id"] is not None]
        assert len(filtered) == 2


class TestStageBLogic:

    def test_daily_aggregation(self):
        from collections import defaultdict

        records = [
            {"order_date": "2024-01-01", "category": "Electronics", "region": "us-east", "order_id": "1", "quantity": 2, "total_amount": 100, "customer_id": "C1"},
            {"order_date": "2024-01-01", "category": "Electronics", "region": "us-east", "order_id": "2", "quantity": 3, "total_amount": 200, "customer_id": "C2"},
            {"order_date": "2024-01-01", "category": "Clothing", "region": "us-east", "order_id": "3", "quantity": 1, "total_amount": 50, "customer_id": "C1"},
        ]

        groups = defaultdict(list)
        for r in records:
            key = (r["order_date"], r["category"], r["region"])
            groups[key].append(r)

        electronics = groups[("2024-01-01", "Electronics", "us-east")]
        assert len(electronics) == 2
        assert sum(r["total_amount"] for r in electronics) == 300
        assert sum(r["quantity"] for r in electronics) == 5
        assert len(set(r["customer_id"] for r in electronics)) == 2

    def test_cumulative_revenue(self):
        daily_revenues = [100, 200, 150, 300]
        cumulative = []
        running = 0
        for rev in daily_revenues:
            running += rev
            cumulative.append(running)

        assert cumulative == [100, 300, 450, 750]
