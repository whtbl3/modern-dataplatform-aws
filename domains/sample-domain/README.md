# Sample Domain (E-commerce Sales)

## Đây là gì?

Đây là domain mẫu mô phỏng dữ liệu bán hàng e-commerce. Nó được dùng để demo toàn bộ data pipeline từ đầu đến cuối: ingest CSV → transform → data quality check → curated Iceberg table → Athena queries.

## Giải quyết vấn đề gì?

- Cung cấp ví dụ cụ thể để team hiểu cách một domain hoạt động
- Dùng để test pipeline trước khi onboard domain thật
- Làm baseline để đo performance và chi phí

## Hoạt động như thế nào?

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

## Cấu trúc

| Folder | Chức năng |
|--------|-----------|
| `data/` | Sample data generator và file CSV output |
| `transforms/stage_a/` | Light transform: schema validation, dedup, format conversion |
| `transforms/stage_b/` | Heavy transform: daily sales aggregation, cumulative revenue |
| `data_quality/` | DQDL rules cho orders_staging và sales_summary tables |
| `athena/` | SQL views để consumers query dữ liệu curated |
