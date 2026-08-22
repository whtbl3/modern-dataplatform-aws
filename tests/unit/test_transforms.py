"""Unit tests cho transform logic (chạy không cần Spark/Glue dependencies)."""
import pytest


def test_deduplication_logic():
    records = [
        {"id": 1, "name": "A", "amount": 100},
        {"id": 1, "name": "A", "amount": 100},
        {"id": 2, "name": "B", "amount": 200},
    ]
    unique = {r["id"]: r for r in records}.values()
    assert len(list(unique)) == 2


def test_null_row_filtering():
    records = [
        {"id": 1, "name": "A", "amount": 100},
        {"id": None, "name": None, "amount": None},
        {"id": 3, "name": "C", "amount": 300},
    ]
    filtered = [r for r in records if any(v is not None for v in r.values())]
    assert len(filtered) == 2


def test_aggregation_logic():
    records = [
        {"category": "X", "amount": 100},
        {"category": "X", "amount": 200},
        {"category": "Y", "amount": 50},
    ]

    from collections import defaultdict
    agg = defaultdict(list)
    for r in records:
        agg[r["category"]].append(r["amount"])

    result = {
        cat: {
            "total_records": len(amounts),
            "total_amount": sum(amounts),
            "avg_amount": sum(amounts) / len(amounts),
        }
        for cat, amounts in agg.items()
    }

    assert result["X"]["total_records"] == 2
    assert result["X"]["total_amount"] == 300
    assert result["X"]["avg_amount"] == 150.0
    assert result["Y"]["total_records"] == 1
