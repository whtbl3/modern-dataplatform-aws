"""
Analytics Stack - Cung cap cong cu cho data consumers query va visualize data.

Tao:
1. Athena Workgroup: Moi truong query co kiem soat chi phi (10 GB scan limit),
   ket qua tu dong luu vao S3 va encrypt, xoa sau 30 ngay
2. QuickSight IAM Role: Cho phep QuickSight doc data tu curated/analytics buckets
   va chay queries qua Athena

Chi phi control: bytes_scanned_cutoff ngan query quet qua nhieu data (tranh bill shock).
Engine version 3: Ho tro Iceberg tables native, khong can plugin.
"""
from aws_cdk import (
    Stack,
    Duration,
    aws_athena as athena,
    aws_quicksight as quicksight,
    aws_s3 as s3,
    aws_iam as iam,
    RemovalPolicy,
)
from constructs import Construct


class AnalyticsStack(Stack):
    """Tao Athena workgroup (cost-controlled) va QuickSight IAM role."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        env_name: str,
        storage_stack,
        **kwargs,
    ):
        super().__init__(scope, construct_id, **kwargs)

        self.athena_results_bucket = s3.Bucket(
            self, "AthenaResultsBucket",
            bucket_name=f"data-platform-athena-results-{env_name}-{self.account}",
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            lifecycle_rules=[
                s3.LifecycleRule(expiration=Duration.days(30)),
            ],
        )

        self.workgroup = athena.CfnWorkGroup(
            self, "AthenaWorkgroup",
            name=f"data-platform-{env_name}",
            description=f"Athena workgroup for data platform ({env_name})",
            state="ENABLED",
            work_group_configuration=athena.CfnWorkGroup.WorkGroupConfigurationProperty(
                result_configuration=athena.CfnWorkGroup.ResultConfigurationProperty(
                    output_location=f"s3://{self.athena_results_bucket.bucket_name}/query-results/",
                    encryption_configuration=athena.CfnWorkGroup.EncryptionConfigurationProperty(
                        encryption_option="SSE_S3",
                    ),
                ),
                enforce_work_group_configuration=True,
                publish_cloud_watch_metrics_enabled=True,
                bytes_scanned_cutoff_per_query=10 * 1024 * 1024 * 1024,  # 10 GB limit
                engine_version=athena.CfnWorkGroup.EngineVersionProperty(
                    selected_engine_version="Athena engine version 3",
                ),
            ),
        )

        self.quicksight_role = iam.Role(
            self, "QuickSightServiceRole",
            role_name=f"data-platform-quicksight-role-{env_name}",
            assumed_by=iam.ServicePrincipal("quicksight.amazonaws.com"),
        )

        storage_stack.curated_bucket.grant_read(self.quicksight_role)
        storage_stack.analytics_bucket.grant_read(self.quicksight_role)
        self.athena_results_bucket.grant_read_write(self.quicksight_role)

        self.quicksight_role.add_to_policy(iam.PolicyStatement(
            actions=[
                "athena:GetQueryExecution",
                "athena:GetQueryResults",
                "athena:StartQueryExecution",
                "athena:StopQueryExecution",
                "glue:GetTable",
                "glue:GetTables",
                "glue:GetDatabase",
                "glue:GetDatabases",
            ],
            resources=["*"],
        ))
