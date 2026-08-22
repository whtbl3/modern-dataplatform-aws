"""
Stream Processor Lambda - Chuyen du lieu real-time tu Kinesis vao S3.

Nhan batch records tu Kinesis (toi da 100 records hoac sau 60 giay),
decode base64, validate JSON, them metadata (_ingested_at, _partition_id),
roi ghi thanh 1 file JSON Lines vao S3 raw zone.

Output path duoc partition theo thoi gian:
  streaming-events/year=2024/month=01/day=15/hour=08/batch_20240115080000_abc12345.json

Records JSON khong hop le bi skip (log warning) nhung khong fail ca batch.
"""
import json
import os
import base64
from datetime import datetime, timezone
import boto3

s3_client = boto3.client("s3")
TARGET_BUCKET = os.environ["TARGET_BUCKET"]
TARGET_PREFIX = os.environ["TARGET_PREFIX"]


def handler(event, context):
    """Decode Kinesis records, validate JSON, ghi batch vao S3 theo time partition."""
    records = event.get("Records", [])
    if not records:
        return {"statusCode": 200, "body": "No records"}

    batch = []
    for record in records:
        payload = base64.b64decode(record["kinesis"]["data"]).decode("utf-8")
        try:
            data = json.loads(payload)
            data["_ingested_at"] = datetime.now(timezone.utc).isoformat()
            data["_partition_id"] = record["kinesis"]["partitionKey"]
            batch.append(data)
        except json.JSONDecodeError:
            print(f"Invalid JSON record skipped: {payload[:100]}")
            continue

    if not batch:
        return {"statusCode": 200, "body": "No valid records"}

    now = datetime.now(timezone.utc)
    key = (
        f"{TARGET_PREFIX}"
        f"year={now.year}/month={now.month:02d}/day={now.day:02d}/"
        f"hour={now.hour:02d}/"
        f"batch_{now.strftime('%Y%m%d%H%M%S')}_{context.aws_request_id[:8]}.json"
    )

    body = "\n".join(json.dumps(record) for record in batch)

    s3_client.put_object(
        Bucket=TARGET_BUCKET,
        Key=key,
        Body=body.encode("utf-8"),
        ContentType="application/json",
    )

    print(f"Wrote {len(batch)} records to s3://{TARGET_BUCKET}/{key}")
    return {"statusCode": 200, "body": f"Processed {len(batch)} records"}
