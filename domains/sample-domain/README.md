# Sample Domain (E-commerce Sales)

## What is this?

Day la domain mau mo phong du lieu ban hang e-commerce. No duoc dung de demo toan bo data pipeline tu dau den cuoi: ingest CSV --> transform --> data quality check --> curated Iceberg table --> Athena queries.

## What problem does it solve?

- Cung cap vi du cu the de team hieu cach mot domain hoat dong
- Dung de test pipeline truoc khi onboard domain that
- Lam baseline de do performance va chi phi

## How does it work?

```
generate_sample.py --> orders.csv --> Upload to S3 Raw
                                          |
                                          v
                            Stage A (validate, dedup, to Iceberg)
                                          |
                                          v
                            Stage B (aggregate by date/category/region)
                                          |
                                          v
                          Athena views (daily_revenue, top_categories, ...)
```

## Structure

| Folder | Chuc nang |
|--------|-----------|
| `data/` | Sample data generator va file CSV output |
| `transforms/stage_a/` | Light transform: schema validation, dedup, format conversion |
| `transforms/stage_b/` | Heavy transform: daily sales aggregation, cumulative revenue |
| `data_quality/` | DQDL rules cho orders_staging va sales_summary tables |
| `athena/` | SQL views de consumers query du lieu curated |
