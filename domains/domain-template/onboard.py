"""
Domain Onboarding Script - Tự động tạo domain mới lên data platform.

Khi một team muốn đưa dữ liệu của họ lên platform, họ chỉ cần chạy script này.
Script sẽ tạo toàn bộ folder structure, config, và boilerplate transform code
để team có thể bắt đầu ngay mà không cần hiểu toàn bộ architecture.

Usage:
    python onboard.py --domain sales --owner sales-team@company.com --dataset transactions

Script tạo:
  domains/{domain_name}/
    ├── config.yaml              # Pipeline config (schedule, workers, governance)
    ├── transforms/stage_a/main.py  # Boilerplate Stage A code (sẵn sàng chạy)
    ├── transforms/stage_b/        # Team tự viết business logic ở đây
    ├── data_quality/              # Team định nghĩa DQ rules ở đây
    ├── athena/                    # SQL views cho consumers
    └── data/                      # Sample data hoặc scripts
"""
import argparse
import shutil
import yaml
from pathlib import Path


def onboard_domain(domain_name: str, owner: str, dataset: str, description: str = ""):
    """Tạo domain folder, generate config.yaml và stage_a boilerplate code."""
    template_dir = Path(__file__).parent
    domains_dir = template_dir.parent
    target_dir = domains_dir / domain_name

    if target_dir.exists():
        print(f"Error: Domain '{domain_name}' already exists at {target_dir}")
        return False

    target_dir.mkdir(parents=True)
    (target_dir / "transforms" / "stage_a").mkdir(parents=True)
    (target_dir / "transforms" / "stage_b").mkdir(parents=True)
    (target_dir / "data_quality").mkdir(parents=True)
    (target_dir / "athena").mkdir(parents=True)
    (target_dir / "data").mkdir(parents=True)

    config = {
        "domain": {
            "name": domain_name,
            "owner": owner,
            "description": description or f"Data domain for {domain_name}",
        },
        "datasets": [{
            "name": dataset,
            "format": "csv",
            "source_prefix": f"{domain_name}/{dataset}/",
            "schema_enforcement": "strict",
            "partition_keys": ["year", "month"],
        }],
        "pipeline": {
            "schedule": "cron(0 7 * * ? *)",
            "timeout_hours": 2,
            "stage_a": {"worker_type": "G.1X", "number_of_workers": 2},
            "stage_b": {"worker_type": "G.1X", "number_of_workers": 4},
        },
        "data_quality": {
            "enabled": True,
            "rules": [
                f'IsComplete "{dataset}_id"',
                f'IsUnique "{dataset}_id"',
                "RowCount > 0",
            ],
        },
        "governance": {
            "classification": "internal",
            "pii_scanning": True,
            "retention_days": 365,
            "access_control": [
                {"role": f"{domain_name}-analysts", "permissions": ["SELECT"]},
                {"role": f"{domain_name}-engineers", "permissions": ["SELECT", "INSERT", "UPDATE", "DELETE"]},
            ],
        },
    }

    config_path = target_dir / "config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    stage_a_code = f'''"""Stage A: Raw ingestion for {domain_name}/{dataset}."""
import sys
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql import functions as F

args = getResolvedOptions(sys.argv, ["JOB_NAME", "source-bucket", "target-bucket", "database-name"])
sc = SparkContext()
glue_context = GlueContext(sc)
spark = glue_context.spark_session
job = Job(glue_context)
job.init(args["JOB_NAME"], args)

source_path = f"s3://{{args[\'source_bucket\']}}/{domain_name}/{dataset}/"
target_table = f"glue_catalog.{{args[\'database_name\']}}.{dataset}_staging"

spark.conf.set("spark.sql.catalog.glue_catalog", "org.apache.iceberg.spark.SparkCatalog")
spark.conf.set("spark.sql.catalog.glue_catalog.warehouse", f"s3://{{args[\'target_bucket\']}}/{domain_name}/")
spark.conf.set("spark.sql.catalog.glue_catalog.catalog-impl", "org.apache.iceberg.aws.glue.GlueCatalog")
spark.conf.set("spark.sql.catalog.glue_catalog.io-impl", "org.apache.iceberg.aws.s3.S3FileIO")

df = spark.read.option("header", "true").option("inferSchema", "true").csv(source_path)
df = df.dropDuplicates(["{dataset}_id"])
df = df.filter(F.col("{dataset}_id").isNotNull())
df = df.withColumn("ingested_at", F.current_timestamp())

df.writeTo(target_table).tableProperty("format-version", "2").createOrReplace()
job.commit()
'''
    (target_dir / "transforms" / "stage_a" / "main.py").write_text(stage_a_code)

    print(f"Domain '{domain_name}' onboarded successfully at {target_dir}")
    print(f"  Config: {config_path}")
    print(f"  Next steps:")
    print(f"    1. Edit transforms/stage_b/main.py for business logic")
    print(f"    2. Update data_quality/rules.py")
    print(f"    3. Commit and push to trigger CI/CD pipeline")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Onboard a new data domain")
    parser.add_argument("--domain", required=True, help="Domain name (e.g. sales, marketing)")
    parser.add_argument("--owner", required=True, help="Team email")
    parser.add_argument("--dataset", required=True, help="Primary dataset name")
    parser.add_argument("--description", default="", help="Domain description")
    args = parser.parse_args()

    onboard_domain(args.domain, args.owner, args.dataset, args.description)
