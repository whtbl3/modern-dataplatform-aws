"""
Governance Stack - Quan ly metadata catalog va access control.

Tao Glue Data Catalog databases (la noi luu thong tin ve tables, schemas, partitions)
va dang ky S3 buckets voi Lake Formation de kiem soat ai duoc doc/ghi data nao.

Glue Catalog giong nhu "muc luc" cua data lake - khong chua data, chi chua
thong tin VE data (ten bang, cot, kieu du lieu, vi tri S3).
Lake Formation la lop access control phia tren - quyet dinh user/role nao
duoc query bang nao, cot nao.
"""
from aws_cdk import (
    Stack,
    aws_lakeformation as lakeformation,
    aws_glue as glue,
    aws_iam as iam,
)
from constructs import Construct


class GovernanceStack(Stack):
    """Tao Glue Catalog databases va dang ky Lake Formation resources."""

    def __init__(self, scope: Construct, construct_id: str, env_name: str, storage_stack, **kwargs):
        """Khoi tao 2 databases (raw + curated) va dang ky buckets voi Lake Formation."""
        super().__init__(scope, construct_id, **kwargs)

        self.database = glue.CfnDatabase(
            self, "GlueDatabase",
            catalog_id=self.account,
            database_input=glue.CfnDatabase.DatabaseInputProperty(
                name=f"data_platform_{env_name}",
                description=f"Main database for data platform ({env_name})",
                location_uri=f"s3://{storage_stack.curated_bucket.bucket_name}/",
            ),
        )

        self.raw_database = glue.CfnDatabase(
            self, "GlueRawDatabase",
            catalog_id=self.account,
            database_input=glue.CfnDatabase.DatabaseInputProperty(
                name=f"data_platform_raw_{env_name}",
                description=f"Raw zone database ({env_name})",
                location_uri=f"s3://{storage_stack.raw_bucket.bucket_name}/",
            ),
        )

        lakeformation.CfnResource(
            self, "LakeFormationRawResource",
            resource_arn=storage_stack.raw_bucket.bucket_arn,
            use_service_linked_role=True,
        )

        lakeformation.CfnResource(
            self, "LakeFormationCuratedResource",
            resource_arn=storage_stack.curated_bucket.bucket_arn,
            use_service_linked_role=True,
        )
