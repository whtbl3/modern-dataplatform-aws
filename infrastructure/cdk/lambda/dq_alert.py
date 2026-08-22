"""
Data Quality Alert Lambda - Thông báo khi dữ liệu không đạt chuẩn.

Được gọi bởi EventBridge khi Glue Data Quality evaluation trả về state=FAILED.
Parse event để lấy danh sách rules bị vi phạm, format thành message đọc được,
rồi gửi qua SNS topic (từ đó đi tới email/Slack/PagerDuty).

Input: EventBridge event từ Glue Data Quality (chứa ruleset name, score, failed rules)
Output: SNS message với subject "[Data Quality FAILED] {ruleset}" và chi tiết rules fail
"""
import json
import os
import boto3

sns_client = boto3.client("sns")
ALERT_TOPIC_ARN = os.environ["ALERT_TOPIC_ARN"]


def handler(event, context):
    """Parse DQ evaluation results, gửi SNS alert với danh sách rules FAIL."""
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
