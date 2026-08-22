"""Unit tests for the streaming processor Lambda function."""
import pytest
import json
import os
import sys
import base64
from unittest.mock import patch, MagicMock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "infrastructure" / "cdk" / "lambda" / "streaming"))


@pytest.fixture(autouse=True)
def set_env():
    os.environ["TARGET_BUCKET"] = "data-platform-raw-dev-123456789012"
    os.environ["TARGET_PREFIX"] = "streaming-events/"
    yield
    del os.environ["TARGET_BUCKET"]
    del os.environ["TARGET_PREFIX"]


@pytest.fixture
def kinesis_event():
    records = [
        {"event_type": "page_view", "user_id": "u123", "page": "/home"},
        {"event_type": "purchase", "user_id": "u456", "amount": 99.99},
    ]
    return {
        "Records": [
            {
                "kinesis": {
                    "data": base64.b64encode(json.dumps(r).encode()).decode(),
                    "partitionKey": f"pk-{i}",
                }
            }
            for i, r in enumerate(records)
        ]
    }


@pytest.fixture
def mock_context():
    ctx = MagicMock()
    ctx.aws_request_id = "abc12345-6789-0000-1111-222233334444"
    return ctx


@patch("boto3.client")
def test_processes_valid_records(mock_boto, kinesis_event, mock_context):
    mock_s3 = MagicMock()
    mock_boto.return_value = mock_s3

    import stream_processor
    stream_processor.s3_client = mock_s3

    result = stream_processor.handler(kinesis_event, mock_context)

    assert result["statusCode"] == 200
    assert "2" in result["body"]
    mock_s3.put_object.assert_called_once()
    call_kwargs = mock_s3.put_object.call_args.kwargs
    assert call_kwargs["Bucket"] == "data-platform-raw-dev-123456789012"
    assert "streaming-events/" in call_kwargs["Key"]


@patch("boto3.client")
def test_handles_empty_records(mock_boto, mock_context):
    mock_s3 = MagicMock()
    mock_boto.return_value = mock_s3

    import stream_processor
    stream_processor.s3_client = mock_s3

    result = stream_processor.handler({"Records": []}, mock_context)

    assert result["statusCode"] == 200
    mock_s3.put_object.assert_not_called()


@patch("boto3.client")
def test_skips_invalid_json(mock_boto, mock_context):
    mock_s3 = MagicMock()
    mock_boto.return_value = mock_s3

    import stream_processor
    stream_processor.s3_client = mock_s3

    event = {
        "Records": [
            {
                "kinesis": {
                    "data": base64.b64encode(b"not-valid-json").decode(),
                    "partitionKey": "pk-0",
                }
            }
        ]
    }

    result = stream_processor.handler(event, mock_context)
    assert result["statusCode"] == 200
    mock_s3.put_object.assert_not_called()
