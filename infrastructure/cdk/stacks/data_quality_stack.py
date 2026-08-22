"""
Data Quality Stack - Đảm bảo dữ liệu đạt chuẩn trước khi vào curated zone.

Tạo:
1. Lambda function nhận event khi Glue Data Quality evaluation FAIL,
   parse danh sách rules bị vi phạm, gửi alert qua SNS
2. EventBridge rule lắng nghe sự kiện "Data Quality Evaluation Results Available"
   với state=FAILED
3. Macie IAM role để scan PII trong raw và curated buckets

Data quality rules (DQDL) được định nghĩa trong domains/*/data_quality/rules.py
và được áp dụng bởi Glue jobs trong pipeline.
"""
from aws_cdk import (
    Stack,
    Duration,
    aws_glue as glue,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_sns as sns,
    aws_sns_subscriptions as subs,
    aws_events as events,
    aws_events_targets as events_targets,
)
from constructs import Construct
from pathlib import Path


class DataQualityStack(Stack):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        env_name: str,
        storage_stack,
        alert_topic: sns.Topic,
        **kwargs,
    ):
        super().__init__(scope, construct_id, **kwargs)

        self.dq_alert_fn = _lambda.Function(
            self, "DataQualityAlertFn",
            function_name=f"data-platform-dq-alert-{env_name}",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="dq_alert.handler",
            code=_lambda.Code.from_asset(str(Path(__file__).parent.parent / "lambda")),
            timeout=Duration.seconds(30),
            memory_size=128,
            environment={
                "ALERT_TOPIC_ARN": alert_topic.topic_arn,
            },
        )

        alert_topic.grant_publish(self.dq_alert_fn)

        events.Rule(
            self, "GlueDataQualityFailRule",
            rule_name=f"data-platform-dq-fail-{env_name}",
            event_pattern=events.EventPattern(
                source=["aws.glue-dataquality"],
                detail_type=["Data Quality Evaluation Results Available"],
                detail={
                    "state": ["FAILED"],
                },
            ),
            targets=[events_targets.LambdaFunction(self.dq_alert_fn)],
        )

        self.macie_role = iam.Role(
            self, "MacieRole",
            role_name=f"data-platform-macie-role-{env_name}",
            assumed_by=iam.ServicePrincipal("macie.amazonaws.com"),
        )

        storage_stack.raw_bucket.grant_read(self.macie_role)
        storage_stack.curated_bucket.grant_read(self.macie_role)
