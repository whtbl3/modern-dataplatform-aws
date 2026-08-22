"""
Data Quality Stack - Dam bao du lieu dat chuan truoc khi vao curated zone.

Tao:
1. Lambda function nhan event khi Glue Data Quality evaluation FAIL,
   parse danh sach rules bi vi pham, gui alert qua SNS
2. EventBridge rule lang nghe su kien "Data Quality Evaluation Results Available"
   voi state=FAILED
3. Macie IAM role de scan PII trong raw va curated buckets

Data quality rules (DQDL) duoc dinh nghia trong domains/*/data_quality/rules.py
va duoc ap dung boi Glue jobs trong pipeline.
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
