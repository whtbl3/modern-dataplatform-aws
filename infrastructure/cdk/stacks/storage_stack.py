"""
Storage Stack - Tang luu tru cua data platform.

Tao 5 S3 buckets theo data lake zones pattern:
- Raw: Du lieu goc chua xu ly (CSV, JSON tu source systems)
- Staging: Du lieu dang duoc xu ly (sau Stage A, truoc Stage B)
- Curated: Du lieu sach, da ap dung business logic, san sang consume
- Analytics: Du lieu da aggregate cho BI dashboards
- Scripts: Chua code cua Glue jobs (deploy tu CI/CD pipeline)

Moi bucket deu co encryption, block public access, va removal policy phu hop.
Raw bucket bat EventBridge notifications de trigger pipeline tu dong.
"""
from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_s3 as s3,
    aws_iam as iam,
)
from constructs import Construct


class StorageStack(Stack):
    """Tao S3 buckets cho data lake zones va IAM role cho Glue."""

    def __init__(self, scope: Construct, construct_id: str, env_name: str, **kwargs):
        """Khoi tao storage resources. Prod buckets duoc RETAIN khi xoa stack."""
        super().__init__(scope, construct_id, **kwargs)

        self.env_name = env_name

        self.raw_bucket = s3.Bucket(
            self, "RawZoneBucket",
            bucket_name=f"data-platform-raw-{env_name}-{self.account}",
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            versioned=True,
            event_bridge_enabled=True,
            removal_policy=RemovalPolicy.RETAIN if env_name == "prod" else RemovalPolicy.DESTROY,
            auto_delete_objects=env_name != "prod",
        )

        self.staging_bucket = s3.Bucket(
            self, "StagingZoneBucket",
            bucket_name=f"data-platform-staging-{env_name}-{self.account}",
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            versioned=False,
            removal_policy=RemovalPolicy.RETAIN if env_name == "prod" else RemovalPolicy.DESTROY,
            auto_delete_objects=env_name != "prod",
        )

        self.curated_bucket = s3.Bucket(
            self, "CuratedZoneBucket",
            bucket_name=f"data-platform-curated-{env_name}-{self.account}",
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            versioned=True,
            removal_policy=RemovalPolicy.RETAIN if env_name == "prod" else RemovalPolicy.DESTROY,
            auto_delete_objects=env_name != "prod",
        )

        self.analytics_bucket = s3.Bucket(
            self, "AnalyticsZoneBucket",
            bucket_name=f"data-platform-analytics-{env_name}-{self.account}",
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            versioned=False,
            removal_policy=RemovalPolicy.RETAIN if env_name == "prod" else RemovalPolicy.DESTROY,
            auto_delete_objects=env_name != "prod",
        )

        self.scripts_bucket = s3.Bucket(
            self, "ScriptsBucket",
            bucket_name=f"data-platform-scripts-{env_name}-{self.account}",
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        self.glue_role = iam.Role(
            self, "GlueServiceRole",
            role_name=f"data-platform-glue-role-{env_name}",
            assumed_by=iam.ServicePrincipal("glue.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSGlueServiceRole"),
            ],
        )

        for bucket in [self.raw_bucket, self.staging_bucket, self.curated_bucket, self.analytics_bucket, self.scripts_bucket]:
            bucket.grant_read_write(self.glue_role)
