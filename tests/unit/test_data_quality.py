"""Unit tests cho data quality rules và alert Lambda."""
import pytest
import json
import os
import sys
from unittest.mock import patch, MagicMock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "infrastructure" / "cdk" / "lambda"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "domains" / "sample-domain" / "data_quality"))


@pytest.fixture(autouse=True)
def set_env():
    os.environ["ALERT_TOPIC_ARN"] = "arn:aws:sns:us-east-1:123456789012:data-platform-alerts-dev"
    yield
    del os.environ["ALERT_TOPIC_ARN"]


class TestDataQualityRules:

    def test_orders_staging_rules_defined(self):
        from rules import ORDERS_STAGING_RULES
        assert "IsComplete" in ORDERS_STAGING_RULES
        assert "IsUnique" in ORDERS_STAGING_RULES
        assert "order_id" in ORDERS_STAGING_RULES
        assert "RowCount > 0" in ORDERS_STAGING_RULES

    def test_sales_summary_rules_defined(self):
        from rules import SALES_SUMMARY_RULES
        assert "total_revenue" in SALES_SUMMARY_RULES
        assert "order_count" in SALES_SUMMARY_RULES
        assert "RowCount > 0" in SALES_SUMMARY_RULES

    def test_validates_positive_amounts(self):
        records = [
            {"order_id": "1", "total_amount": 100},
            {"order_id": "2", "total_amount": -5},
            {"order_id": "3", "total_amount": 0},
        ]
        valid = [r for r in records if r["total_amount"] > 0]
        assert len(valid) == 1


class TestDataQualityAlert:

    @patch("boto3.client")
    def test_sends_alert_on_failure(self, mock_boto):
        mock_sns = MagicMock()
        mock_boto.return_value = mock_sns

        import dq_alert
        dq_alert.sns_client = mock_sns

        event = {
            "detail": {
                "rulesetNames": ["orders_staging_rules"],
                "state": "FAILED",
                "score": 0.75,
                "rulesetEvaluationResults": [
                    {"rule": "IsComplete 'order_id'", "result": "PASS"},
                    {"rule": "IsUnique 'order_id'", "result": "FAIL"},
                    {"rule": "RowCount > 0", "result": "FAIL"},
                ],
            }
        }

        result = dq_alert.handler(event, None)

        assert result["statusCode"] == 200
        mock_sns.publish.assert_called_once()
        call_kwargs = mock_sns.publish.call_args.kwargs
        assert "FAILED" in call_kwargs["Subject"]
        assert "IsUnique" in call_kwargs["Message"]
        assert "RowCount" in call_kwargs["Message"]
