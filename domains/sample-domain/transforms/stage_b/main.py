"""Stage B: Business logic transform - staging to curated zone.

Performs:
- Joins and enrichment
- Business aggregations (daily sales by category/region)
- Partitioned write to curated Iceberg table
"""
import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql import functions as F
from pyspark.sql.window import Window

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

source_table = f"glue_catalog.{args['database_name']}.orders_staging"
target_table = f"glue_catalog.{args['database_name']}.sales_summary"

spark.conf.set("spark.sql.catalog.glue_catalog", "org.apache.iceberg.spark.SparkCatalog")
spark.conf.set("spark.sql.catalog.glue_catalog.warehouse", f"s3://{args['target_bucket']}/sample-domain/")
spark.conf.set("spark.sql.catalog.glue_catalog.catalog-impl", "org.apache.iceberg.aws.glue.GlueCatalog")
spark.conf.set("spark.sql.catalog.glue_catalog.io-impl", "org.apache.iceberg.aws.s3.S3FileIO")

df = spark.table(source_table)

daily_sales = df.groupBy(
    F.col("order_date"),
    F.col("category"),
    F.col("region"),
).agg(
    F.count("order_id").alias("order_count"),
    F.sum("quantity").alias("total_quantity"),
    F.sum("total_amount").alias("total_revenue"),
    F.avg("total_amount").alias("avg_order_value"),
    F.countDistinct("customer_id").alias("unique_customers"),
)

daily_sales = daily_sales \
    .withColumn("year", F.year("order_date")) \
    .withColumn("month", F.month("order_date")) \
    .withColumn("processed_at", F.current_timestamp())

window = Window.partitionBy("category", "region").orderBy("order_date")
daily_sales = daily_sales.withColumn(
    "cumulative_revenue",
    F.sum("total_revenue").over(window),
)

daily_sales.writeTo(target_table) \
    .tableProperty("format-version", "2") \
    .tableProperty("write.format.default", "parquet") \
    .partitionedBy(F.years("order_date")) \
    .createOrReplace()

print(f"Stage B complete: {daily_sales.count()} summary records written to {target_table}")

job.commit()
