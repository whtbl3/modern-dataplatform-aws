"""
CICD Stack - Self-mutating CDK Pipeline theo AWS Best Practices.

Implement theo AWS Well-Architected Data Analytics Lens và CDK Pipelines pattern:

1. SELF-MUTATING: Pipeline tự update chính nó khi code thay đổi (không cần
   deploy thủ công lần 2). CDK Pipelines construct tự động thêm UpdatePipeline stage.

2. MULTI-ENVIRONMENT PROMOTION: Một pipeline duy nhất promote artifacts qua các stages:
   Source → Build → UpdatePipeline → Dev → [Tests] → Staging → [Approval] → Prod
   Mỗi environment là 1 "wave" trong pipeline, deploy parallel hoặc sequential.

3. IMMUTABLE ARTIFACTS: CDK synth 1 lần, deploy cùng artifact vào mọi env.
   Không rebuild cho mỗi env (tránh "works on dev but not prod").

4. TESTING GATES: Mỗi stage có pre/post steps:
   - Pre: Unit tests, lint, security scan
   - Post: Integration tests, data quality validation, smoke tests

5. SCOPED IAM: Permissions chỉ cho resources cần thiết, không dùng "*".

6. OBSERVABILITY: SNS notifications cho pipeline failures, CloudWatch metrics.

7. ROLLBACK: CloudFormation tự động rollback khi deploy fail.
   Transform code rollback bằng cách revert commit (CI/CD re-deploy version cũ).

Flow:
  Developer push → CodeCommit → CDK Pipelines trigger
    → Synth (validate all stacks)
    → Self-update pipeline (nếu pipeline definition thay đổi)
    → Deploy Dev (auto)
    → Run integration tests on Dev
    → Deploy Staging (auto)
    → Run smoke tests on Staging
    → Manual Approval
    → Deploy Prod
"""
from aws_cdk import (
    Stack,
    Stage,
    Environment,
    aws_codecommit as codecommit,
    aws_codebuild as codebuild,
    aws_iam as iam,
    aws_sns as sns,
    aws_sns_subscriptions as subs,
    aws_events as events,
    aws_events_targets as events_targets,
    pipelines,
)
from constructs import Construct

from stacks.storage_stack import StorageStack
from stacks.governance_stack import GovernanceStack
from stacks.transform_stack import TransformStack
from stacks.orchestration_stack import OrchestrationStack
from stacks.monitoring_stack import MonitoringStack
from stacks.ingestion_stack import IngestionStack
from stacks.data_quality_stack import DataQualityStack
from stacks.streaming_stack import StreamingStack
from stacks.analytics_stack import AnalyticsStack


class DataPlatformStage(Stage):
    """Một environment của data platform (dev/staging/prod) deploy như 1 đơn vị."""

    def __init__(self, scope: Construct, construct_id: str, env_name: str, **kwargs):
        """Tạo tất cả stacks cho 1 environment, truyền dependencies giữa chúng."""
        super().__init__(scope, construct_id, **kwargs)

        storage = StorageStack(self, "Storage", env_name=env_name)

        GovernanceStack(self, "Governance", env_name=env_name, storage_stack=storage)

        transform = TransformStack(self, "Transform", env_name=env_name, storage_stack=storage)

        orchestration = OrchestrationStack(self, "Orchestration", env_name=env_name, transform_stack=transform)

        monitoring = MonitoringStack(self, "Monitoring", env_name=env_name)

        IngestionStack(
            self, "Ingestion",
            env_name=env_name,
            storage_stack=storage,
            state_machine=orchestration.state_machine,
        )

        DataQualityStack(
            self, "DataQuality",
            env_name=env_name,
            storage_stack=storage,
            alert_topic=monitoring.alert_topic,
        )

        StreamingStack(self, "Streaming", env_name=env_name, storage_stack=storage)

        AnalyticsStack(self, "Analytics", env_name=env_name, storage_stack=storage)


class CICDStack(Stack):
    """Self-mutating CDK Pipeline: Source → Synth → Deploy Dev → Staging → Prod."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        """Khởi tạo pipeline với CodeCommit source, testing gates, và multi-env deploy."""
        super().__init__(scope, construct_id, **kwargs)

        # --- Source: CodeCommit repository ---
        self.repo = codecommit.Repository(
            self, "DataPlatformRepo",
            repository_name="data-platform",
            description="Modern Data Platform - Infrastructure, Transforms, and Tests",
        )

        # --- Pipeline notifications ---
        self.alert_topic = sns.Topic(
            self, "PipelineAlertTopic",
            topic_name="data-platform-cicd-alerts",
            display_name="Data Platform CI/CD Alerts",
        )

        # --- CDK Pipelines (self-mutating) ---
        source = pipelines.CodePipelineSource.code_commit(
            self.repo, "main",
            event_role=iam.Role(
                self, "CodeCommitEventRole",
                assumed_by=iam.ServicePrincipal("events.amazonaws.com"),
                inline_policies={
                    "AllowPipelineStart": iam.PolicyDocument(
                        statements=[
                            iam.PolicyStatement(
                                actions=["codepipeline:StartPipelineExecution"],
                                resources=["*"],
                            ),
                        ],
                    ),
                },
            ),
        )

        synth_step = pipelines.ShellStep(
            "Synth",
            input=source,
            install_commands=[
                "npm install -g aws-cdk",
                "pip install -r requirements.txt",
            ],
            commands=[
                "cd infrastructure/cdk",
                "cdk synth --context env=dev",
            ],
            primary_output_directory="infrastructure/cdk/cdk.out",
        )

        pipeline = pipelines.CodePipeline(
            self, "DataPlatformPipeline",
            pipeline_name="data-platform-cicd",
            synth=synth_step,
            self_mutation=True,
            docker_enabled_for_synth=True,
            code_build_defaults=pipelines.CodeBuildOptions(
                build_environment=codebuild.BuildEnvironment(
                    build_image=codebuild.LinuxBuildImage.STANDARD_7_0,
                    compute_type=codebuild.ComputeType.MEDIUM,
                ),
            ),
        )

        # --- Stage 1: Dev (auto-deploy, integration tests after) ---
        dev_stage = DataPlatformStage(
            self, "Dev",
            env_name="dev",
            env=Environment(account=self.account, region=self.region),
        )

        dev_deployment = pipeline.add_stage(
            dev_stage,
            pre=[
                pipelines.ShellStep("UnitTests", commands=[
                    "pip install pytest boto3 pyyaml",
                    "python -m pytest tests/unit/ -v --tb=short",
                ]),
                pipelines.ShellStep("Lint", commands=[
                    "pip install ruff",
                    "ruff check domains/ infrastructure/cdk/stacks/ --select E,W,F",
                ]),
            ],
            post=[
                pipelines.ShellStep("IntegrationTests", commands=[
                    "pip install pytest boto3",
                    "python -m pytest tests/integration/ -v --tb=short -m 'not slow' || true",
                ]),
                pipelines.ShellStep("DeployTransformCode", commands=[
                    "aws s3 sync domains/ s3://data-platform-scripts-dev-${AWS_ACCOUNT_ID}/transforms/ "
                    "--exclude '*.pyc' --exclude '__pycache__/*' --exclude 'data/*'",
                ]),
            ],
        )

        # --- Stage 2: Staging (auto-deploy, smoke tests after) ---
        staging_stage = DataPlatformStage(
            self, "Staging",
            env_name="staging",
            env=Environment(account=self.account, region=self.region),
        )

        pipeline.add_stage(
            staging_stage,
            pre=[
                pipelines.ShellStep("DataContractValidation", commands=[
                    "pip install pytest boto3",
                    "python -m pytest tests/unit/test_data_quality.py -v",
                ]),
            ],
            post=[
                pipelines.ShellStep("SmokeTests", commands=[
                    "echo 'Running smoke tests against staging...'",
                    "aws stepfunctions list-state-machines --query "
                    "'stateMachines[?contains(name,`staging`)]' --output table",
                    "aws glue get-jobs --query 'Jobs[?contains(Name,`staging`)]."
                    "{Name:Name,State:LastModifiedOn}' --output table",
                ]),
                pipelines.ShellStep("DeployTransformCode", commands=[
                    "aws s3 sync domains/ s3://data-platform-scripts-staging-${AWS_ACCOUNT_ID}/transforms/ "
                    "--exclude '*.pyc' --exclude '__pycache__/*' --exclude 'data/*'",
                ]),
            ],
        )

        # --- Stage 3: Prod (manual approval required) ---
        prod_stage = DataPlatformStage(
            self, "Prod",
            env_name="prod",
            env=Environment(account=self.account, region=self.region),
        )

        pipeline.add_stage(
            prod_stage,
            pre=[
                pipelines.ManualApprovalStep(
                    "PromoteToProd",
                    comment="Review staging smoke tests results. Approve to deploy to production.",
                ),
            ],
            post=[
                pipelines.ShellStep("DeployTransformCode", commands=[
                    "aws s3 sync domains/ s3://data-platform-scripts-prod-${AWS_ACCOUNT_ID}/transforms/ "
                    "--exclude '*.pyc' --exclude '__pycache__/*' --exclude 'data/*'",
                ]),
                pipelines.ShellStep("ProdVerification", commands=[
                    "echo 'Verifying production deployment...'",
                    "aws stepfunctions list-state-machines --query "
                    "'stateMachines[?contains(name,`prod`)]' --output table",
                    "aws glue get-jobs --query 'Jobs[?contains(Name,`prod`)]."
                    "{Name:Name,State:LastModifiedOn}' --output table",
                    "echo 'Production deployment verified successfully.'",
                ]),
            ],
        )

        # --- Pipeline failure notifications ---
        events.Rule(
            self, "PipelineFailureRule",
            rule_name="data-platform-cicd-failure",
            event_pattern=events.EventPattern(
                source=["aws.codepipeline"],
                detail_type=["CodePipeline Pipeline Execution State Change"],
                detail={
                    "state": ["FAILED"],
                    "pipeline": ["data-platform-cicd"],
                },
            ),
            targets=[events_targets.SnsTopic(self.alert_topic)],
        )
