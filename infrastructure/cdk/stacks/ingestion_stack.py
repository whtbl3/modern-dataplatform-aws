"""
Ingestion Stack - Tu dong trigger pipeline khi co data moi.

Tao EventBridge rule lang nghe su kien "Object Created" tu S3 raw bucket.
Khi file .csv moi upload vao prefix "sample-domain/", EventBridge trigger Lambda.
Lambda parse event va start Step Functions execution.

Dung EventBridge thay vi S3 Notification truc tiep de tranh dependency cycle
giua Storage stack va Ingestion stack (S3 bucket khong can biet ve Lambda).
"""
from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_s3 as s3,
    aws_events as events,
    aws_events_targets as events_targets,
    aws_stepfunctions as sfn,
)
from constructs import Construct
from pathlib import Path


class IngestionStack(Stack):
    """Tao Lambda trigger va EventBridge rule cho S3 file ingestion."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        env_name: str,
        storage_stack,
        state_machine: sfn.StateMachine,
        **kwargs,
    ):
        super().__init__(scope, construct_id, **kwargs)

        self.trigger_fn = _lambda.Function(
            self, "TriggerPipelineFn",
            function_name=f"data-platform-trigger-pipeline-{env_name}",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="trigger_pipeline.handler",
            code=_lambda.Code.from_asset(str(Path(__file__).parent.parent / "lambda")),
            timeout=Duration.seconds(30),
            memory_size=128,
            environment={
                "STATE_MACHINE_ARN": state_machine.state_machine_arn,
            },
        )

        state_machine.grant_start_execution(self.trigger_fn)

        self.trigger_fn.add_to_role_policy(iam.PolicyStatement(
            actions=["s3:GetObject", "s3:ListBucket"],
            resources=[
                storage_stack.raw_bucket.bucket_arn,
                f"{storage_stack.raw_bucket.bucket_arn}/*",
            ],
        ))

        events.Rule(
            self, "S3ObjectCreatedRule",
            rule_name=f"data-platform-s3-trigger-{env_name}",
            event_pattern=events.EventPattern(
                source=["aws.s3"],
                detail_type=["Object Created"],
                detail={
                    "bucket": {"name": [storage_stack.raw_bucket.bucket_name]},
                    "object": {"key": [{"prefix": "sample-domain/"}, {"suffix": ".csv"}]},
                },
            ),
            targets=[events_targets.LambdaFunction(self.trigger_fn)],
        )
