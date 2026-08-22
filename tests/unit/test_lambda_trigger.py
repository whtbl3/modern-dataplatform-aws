"""Unit tests for the pipeline trigger Lambda function."""
import pytest
import json
import os
import sys
from unittest.mock import patch, MagicMock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "infrastructure" / "cdk" / "lambda"))


@pytest.fixture(autouse=True)
def set_env():
    os.environ["STATE_MACHINE_ARN"] = "arn:aws:states:us-east-1:123456789012:stateMachine:test"
    yield
    del os.environ["STATE_MACHINE_ARN"]


@pytest.fixture
def s3_event():
    return {
        "Records": [
            {
                "s3": {
                    "bucket": {"name": "data-platform-raw-dev-123456789012"},
                    "object": {"key": "sample-domain/orders/orders_2024.csv"},
                }
            }
        ]
    }


@pytest.fixture
def non_csv_event():
    return {
        "Records": [
            {
                "s3": {
                    "bucket": {"name": "data-platform-raw-dev-123456789012"},
                    "object": {"key": "sample-domain/orders/metadata.json"},
                }
            }
        ]
    }


@patch("boto3.client")
def test_trigger_starts_execution(mock_boto_client, s3_event):
    mock_sfn = MagicMock()
    mock_sfn.start_execution.return_value = {
        "executionArn": "arn:aws:states:us-east-1:123456789012:execution:test:run-1"
    }
    mock_boto_client.return_value = mock_sfn

    import trigger_pipeline
    trigger_pipeline.sfn_client = mock_sfn

    result = trigger_pipeline.handler(s3_event, None)

    mock_sfn.start_execution.assert_called_once()
    call_args = mock_sfn.start_execution.call_args
    assert call_args.kwargs["stateMachineArn"] == os.environ["STATE_MACHINE_ARN"]

    input_data = json.loads(call_args.kwargs["input"])
    assert input_data["source_bucket"] == "data-platform-raw-dev-123456789012"
    assert input_data["source_key"] == "sample-domain/orders/orders_2024.csv"
    assert input_data["domain"] == "sample-domain"
    assert result["statusCode"] == 200


@patch("boto3.client")
def test_skips_non_csv_files(mock_boto_client, non_csv_event):
    mock_sfn = MagicMock()
    mock_boto_client.return_value = mock_sfn

    import trigger_pipeline
    trigger_pipeline.sfn_client = mock_sfn

    result = trigger_pipeline.handler(non_csv_event, None)

    mock_sfn.start_execution.assert_not_called()
    assert result["statusCode"] == 200
