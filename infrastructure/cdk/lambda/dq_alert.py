"""
Data Quality Alert Lambda - Thong bao khi du lieu khong dat chuan.

Duoc goi boi EventBridge khi Glue Data Quality evaluation tra ve state=FAILED.
Parse event de lay danh sach rules bi vi pham, format thanh message doc duoc,
roi gui qua SNS topic (tu do di toi email/Slack/PagerDuty).

Input: EventBridge event tu Glue Data Quality (chua ruleset name, score, failed rules)
Output: SNS message voi subject "[Data Quality FAILED] {ruleset}" va chi tiet rules fail
"""
import json
import os
import boto3

sns_client = boto3.client("sns")
ALERT_TOPIC_ARN = os.environ["ALERT_TOPIC_ARN"]


def handler(event, context):
    """Parse DQ evaluation results, gui SNS alert voi danh sach rules FAIL."""
    detail = event.get("detail", {})
    ruleset_name = detail.get("rulesetNames", ["unknown"])[0]
    state = detail.get("state", "UNKNOWN")
    score = detail.get("score", 0)
    outcomes = detail.get("rulesetEvaluationResults", [])

    failed_rules = [
        r["rule"] for r in outcomes
        if r.get("result") == "FAIL"
    ]

    subject = f"[Data Quality FAILED] {ruleset_name}"
    message = (
        f"Data Quality Check Failed\n"
        f"{'=' * 40}\n"
        f"Ruleset: {ruleset_name}\n"
        f"State: {state}\n"
        f"Score: {score:.1%}\n"
        f"\nFailed Rules ({len(failed_rules)}):\n"
    )
    for rule in failed_rules:
        message += f"  - {rule}\n"

    sns_client.publish(
        TopicArn=ALERT_TOPIC_ARN,
        Subject=subject[:100],
        Message=message,
    )

    print(f"Alert sent for {ruleset_name}: {len(failed_rules)} failed rules")
    return {"statusCode": 200}
