"""
Governance Stack - Quản lý metadata catalog và access control.

Tạo Glue Data Catalog databases (là nơi lưu thông tin về tables, schemas, partitions)
và đăng ký S3 buckets với Lake Formation để kiểm soát ai được đọc/ghi data nào.

Glue Catalog giống như "mục lục" của data lake - không chứa data, chỉ chứa
thông tin VỀ data (tên bảng, cột, kiểu dữ liệu, vị trí S3).
Lake Formation là lớp access control phía trên - quyết định user/role nào
được query bảng nào, cột nào.
"""
from aws_cdk import (
    Stack,
    aws_lakeformation as lakeformation,
    aws_glue as glue,
    aws_iam as iam,
)
from constructs import Construct


class GovernanceStack(Stack):
    """Tạo Glue Catalog databases và đăng ký Lake Formation resources."""

    def __init__(self, scope: Construct, construct_id: str, env_name: str, storage_stack, **kwargs):
        """Khởi tạo 2 databases (raw + curated) và đăng ký buckets với Lake Formation."""
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
