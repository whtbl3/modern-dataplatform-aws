"""Stage A: Nạp CSV thô → Iceberg table trong staging zone.

Thực hiện:
- Kiểm tra schema
- Ép kiểu dữ liệu
- Loại bỏ bản ghi trùng lặp
- Ghi ra định dạng Iceberg
"""
import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType, DoubleType, DateType,
)

args = getResolvedOptions(sys.argv, [
    "JOB_NAME",
    "source-bucket",
    "target-bucket",
    "database-name",
])

sc = SparkContext()
glue_context = GlueContext(sc)
spark = glue_context.spark_session
job = Job(glue_context)
job.init(args["JOB_NAME"], args)

source_path = f"s3://{args['source_bucket']}/sample-domain/orders/"
target_table = f"glue_catalog.{args['database_name']}.orders_staging"

ORDERS_SCHEMA = StructType([
    StructField("order_id", StringType(), nullable=False),
    StructField("order_date", DateType(), nullable=False),
    StructField("customer_id", StringType(), nullable=False),
    StructField("category", StringType(), nullable=True),
    StructField("product_name", StringType(), nullable=True),
    StructField("quantity", IntegerType(), nullable=True),
    StructField("unit_price", DoubleType(), nullable=True),
    StructField("total_amount", DoubleType(), nullable=True),
    StructField("region", StringType(), nullable=True),
    StructField("payment_method", StringType(), nullable=True),
])

spark.conf.set("spark.sql.catalog.glue_catalog", "org.apache.iceberg.spark.SparkCatalog")
spark.conf.set("spark.sql.catalog.glue_catalog.warehouse", f"s3://{args['target_bucket']}/sample-domain/")
spark.conf.set("spark.sql.catalog.glue_catalog.catalog-impl", "org.apache.iceberg.aws.glue.GlueCatalog")
spark.conf.set("spark.sql.catalog.glue_catalog.io-impl", "org.apache.iceberg.aws.s3.S3FileIO")

df = spark.read \
    .option("header", "true") \
    .schema(ORDERS_SCHEMA) \
    .csv(source_path)

df = df.dropDuplicates(["order_id"])
df = df.filter(F.col("order_id").isNotNull())
df = df.withColumn("ingested_at", F.current_timestamp())

df.writeTo(target_table) \
    .tableProperty("format-version", "2") \
    .tableProperty("write.format.default", "parquet") \
    .createOrReplace()

print(f"Stage A complete: {df.count()} records written to {target_table}")

job.commit()
