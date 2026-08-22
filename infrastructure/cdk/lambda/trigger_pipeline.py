"""
Pipeline Trigger Lambda - Khoi dong ETL pipeline khi co file moi trong S3.

Duoc goi boi EventBridge khi S3 raw bucket nhan file .csv moi.
Chi xu ly file CSV, bo qua cac dinh dang khac (JSON metadata, Parquet, ...).
Moi file CSV trigger 1 Step Functions execution rieng biet.

Input: EventBridge event chua thong tin bucket va object key
Output: Start Step Functions execution voi context (bucket, key, domain name)
"""
import json
import os
import boto3

sfn_client = boto3.client("stepfunctions")
STATE_MACHINE_ARN = os.environ["STATE_MACHINE_ARN"]


def handler(event, context):
    """Xu ly S3 event records, start pipeline cho moi file CSV."""
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
