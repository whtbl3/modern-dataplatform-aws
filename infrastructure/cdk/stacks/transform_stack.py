"""
Transform Stack - Glue ETL jobs xu ly du lieu.

Tao 2 Glue jobs theo SDLF pattern (Serverless Data Lake Framework):
- Stage A: Light transform - doc raw data, validate schema, dedup, ghi Iceberg
- Stage B: Heavy transform - join datasets, ap dung business logic, aggregate

Con tao 1 Crawler chay hang ngay de cap nhat Glue Catalog voi tables/partitions moi.

Glue jobs doc script tu S3 scripts bucket (deploy boi CI/CD pipeline),
nen khi data engineer update code chi can commit, khong can sua infrastructure.
"""
from aws_cdk import (
    Stack,
    aws_glue as glue,
)
from constructs import Construct


class TransformStack(Stack):
    """Tao Glue ETL jobs (Stage A + B) va Crawler cho curated zone."""

    def __init__(self, scope: Construct, construct_id: str, env_name: str, storage_stack, **kwargs):
        """Khoi tao Glue jobs voi Iceberg support va CloudWatch logging."""
        super().__init__(scope, construct_id, **kwargs)

        self.stage_a_job = glue.CfnJob(
            self, "StageAJob",
            name=f"data-platform-stage-a-{env_name}",
            role=storage_stack.glue_role.role_arn,
            description="Stage A: Light transform - format conversion and schema validation",
            glue_version="4.0",
            worker_type="G.1X",
            number_of_workers=2,
            command=glue.CfnJob.JobCommandProperty(
                name="glueetl",
                python_version="3",
                script_location=f"s3://{storage_stack.scripts_bucket.bucket_name}/transforms/stage_a/main.py",
            ),
            default_arguments={
                "--job-language": "python",
                "--enable-metrics": "true",
                "--enable-continuous-cloudwatch-log": "true",
                "--source-bucket": storage_stack.raw_bucket.bucket_name,
                "--target-bucket": storage_stack.staging_bucket.bucket_name,
                "--datalake-formats": "iceberg",
            },
        )

        self.stage_b_job = glue.CfnJob(
            self, "StageBJob",
            name=f"data-platform-stage-b-{env_name}",
            role=storage_stack.glue_role.role_arn,
            description="Stage B: Heavy transform - joins, business logic, aggregations",
            glue_version="4.0",
            worker_type="G.1X",
            number_of_workers=4,
            command=glue.CfnJob.JobCommandProperty(
                name="glueetl",
                python_version="3",
                script_location=f"s3://{storage_stack.scripts_bucket.bucket_name}/transforms/stage_b/main.py",
            ),
            default_arguments={
                "--job-language": "python",
                "--enable-metrics": "true",
                "--enable-continuous-cloudwatch-log": "true",
                "--source-bucket": storage_stack.staging_bucket.bucket_name,
                "--target-bucket": storage_stack.curated_bucket.bucket_name,
                "--datalake-formats": "iceberg",
            },
        )

        self.crawler = glue.CfnCrawler(
            self, "CuratedCrawler",
            name=f"data-platform-curated-crawler-{env_name}",
            role=storage_stack.glue_role.role_arn,
            database_name=f"data_platform_{env_name}",
            targets=glue.CfnCrawler.TargetsProperty(
                s3_targets=[
                    glue.CfnCrawler.S3TargetProperty(
                        path=f"s3://{storage_stack.curated_bucket.bucket_name}/",
                    ),
                ],
            ),
            schedule=glue.CfnCrawler.ScheduleProperty(
                schedule_expression="cron(0 6 * * ? *)",
            ),
        )
