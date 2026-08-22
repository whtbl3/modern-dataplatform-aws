"""
Pipeline Trigger Lambda - Khởi động ETL pipeline khi có file mới trong S3.

Được gọi bởi EventBridge khi S3 raw bucket nhận file .csv mới.
Chỉ xử lý file CSV, bỏ qua các định dạng khác (JSON metadata, Parquet, ...).
Mỗi file CSV trigger 1 Step Functions execution riêng biệt.

Input: EventBridge event chứa thông tin bucket và object key
Output: Start Step Functions execution với context (bucket, key, domain name)
"""
import json
import os
import boto3

sfn_client = boto3.client("stepfunctions")
STATE_MACHINE_ARN = os.environ["STATE_MACHINE_ARN"]


def handler(event, context):
    """Xử lý S3 event records, start pipeline cho mỗi file CSV."""
    for record in event["Records"]:
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]

        if not key.endswith(".csv"):
            print(f"Skipping non-CSV file: {key}")
            continue

        print(f"New file detected: s3://{bucket}/{key}")

        execution_input = json.dumps({
            "source_bucket": bucket,
            "source_key": key,
            "domain": key.split("/")[0] if "/" in key else "unknown",
        })

        response = sfn_client.start_execution(
            stateMachineArn=STATE_MACHINE_ARN,
            input=execution_input,
        )

        print(f"Pipeline triggered: {response['executionArn']}")

    return {"statusCode": 200, "body": "Pipeline triggered"}
