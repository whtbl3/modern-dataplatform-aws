# Tổng quan Data Platform - Kiến trúc & Luồng xử lý

## Vấn đề mà platform giải quyết

```
TRƯỚC KHI CÓ PLATFORM:

  Team Sales       Team Marketing      Team Finance
      │                  │                   │
      ▼                  ▼                   ▼
  Excel files      Google Sheets        CSV exports
      │                  │                   │
      ▼                  ▼                   ▼
  Gửi email       Copy-paste           Chạy script thủ công
      │                  │                   │
      └──────────────────┼───────────────────┘
                         ▼
              ❌ Không ai biết data ở đâu
              ❌ Mỗi team format khác nhau
              ❌ Không kiểm soát chất lượng
              ❌ Không có lịch sử thay đổi
              ❌ Muốn dùng data team khác → chờ hàng tuần
```

```
SAU KHI CÓ PLATFORM:

  Team Sales       Team Marketing      Team Finance
      │                  │                   │
      ▼                  ▼                   ▼
  Upload CSV          Kinesis             Upload CSV
  vào S3 raw         stream              vào S3 raw
      │                  │                   │
      └──────────────────┼───────────────────┘
                         ▼
              ┌─────────────────────┐
              │   DATA PLATFORM     │
              │  (tự động xử lý)    │
              └─────────────────────┘
                         │
                         ▼
              ✅ Dữ liệu tập trung 1 nơi
              ✅ Chuẩn hoá format (Iceberg)
              ✅ Kiểm tra chất lượng tự động
              ✅ Lịch sử đầy đủ (versioned)
              ✅ Self-service: query ngay qua Athena
```

---

## 10 Stacks và vai trò của từng stack

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        MODERN DATA PLATFORM                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ① STORAGE          Nền tảng lưu trữ - 5 S3 buckets theo zones             │
│       │                                                                      │
│  ② GOVERNANCE       Quản trị - ai được đọc/ghi data nào                    │
│       │                                                                      │
│  ③ INGESTION        Tiếp nhận - tự động phát hiện data mới                 │
│       │                                                                      │
│  ④ TRANSFORM        Biến đổi - từ raw thành curated (Stage A + B)          │
│       │                                                                      │
│  ⑤ ORCHESTRATION    Điều phối - chạy đúng thứ tự, xử lý lỗi              │
│       │                                                                      │
│  ⑥ DATA QUALITY     Chất lượng - chặn data xấu trước khi vào curated      │
│       │                                                                      │
│  ⑦ STREAMING        Thời gian thực - Kinesis → Lambda → S3                 │
│       │                                                                      │
│  ⑧ ANALYTICS        Tiêu thụ - Athena queries + QuickSight dashboards      │
│       │                                                                      │
│  ⑨ MONITORING       Giám sát - alarms + dashboard + alerts                 │
│       │                                                                      │
│  ⑩ CICD             Triển khai - tự động deploy qua 3 environments         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Chi tiết từng stack

| # | Stack | Vấn đề giải quyết | Cách giải quyết | AWS Services |
|---|-------|-------------------|-----------------|--------------|
| ① | **Storage** | Dữ liệu nằm rải rác, không có nơi tập trung | 5 S3 buckets chia theo mức độ xử lý (raw → staging → curated → analytics) | S3, IAM |
| ② | **Governance** | Không kiểm soát ai đọc/ghi gì, thiếu metadata | Glue Catalog lưu schema, Lake Formation kiểm soát quyền truy cập theo cột/bảng | Glue Catalog, Lake Formation |
| ③ | **Ingestion** | Phải trigger pipeline thủ công mỗi khi có data mới | EventBridge tự phát hiện file mới trong S3, Lambda tự khởi động pipeline | EventBridge, Lambda |
| ④ | **Transform** | Xử lý data thủ công, không có chuẩn hoá | 2 Glue jobs (Stage A: validate + dedup, Stage B: business logic) ghi ra Iceberg | Glue ETL, Iceberg |
| ⑤ | **Orchestration** | Chạy sai thứ tự, không xử lý lỗi | Step Functions đảm bảo A→B tuần tự, fail thì dừng và báo lỗi | Step Functions, EventBridge |
| ⑥ | **Data Quality** | Data xấu lọt vào curated zone, báo cáo sai | DQDL rules kiểm tra sau mỗi transform, alert ngay khi fail | Glue DQ, Lambda, SNS |
| ⑦ | **Streaming** | Chỉ xử lý batch, không hỗ trợ real-time | Kinesis stream + Lambda processor ghi vào S3 raw theo time partition | Kinesis, Lambda |
| ⑧ | **Analytics** | Muốn query data phải nhờ engineer viết script | Athena cho phép anyone query bằng SQL, QuickSight cho dashboard tự phục vụ | Athena, QuickSight |
| ⑨ | **Monitoring** | Không biết pipeline fail khi nào, phải đợi user báo | CloudWatch alarms + SNS alert ngay khi Glue/Step Functions fail | CloudWatch, SNS |
| ⑩ | **CICD** | Deploy thủ công hay lỗi, "works on my machine" | CDK Pipelines tự deploy qua Dev→Staging→Prod, immutable artifacts | CodePipeline, CodeBuild |

---

## Luồng xử lý End-to-End (Batch)

Đây là luồng hoàn chỉnh từ khi data được upload đến khi user query kết quả.

```
                    ┌───────────────┐
                    │  Data Source  │
                    │  (CSV file)   │
                    └───────┬───────┘
                            │ Upload vào S3
                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ ① STORAGE: S3 Raw Bucket                                                │
│    s3://data-platform-raw-{env}-{account}/sample-domain/orders.csv      │
│    • Encrypted (SSE-S3)                                                  │
│    • Versioned (có thể rollback)                                         │
│    • EventBridge enabled → phát event khi có object mới                  │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │ S3 phát event "Object Created"
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ ③ INGESTION: EventBridge Rule + Lambda                                   │
│                                                                          │
│    EventBridge Rule:                                                     │
│      source: aws.s3                                                      │
│      detail-type: Object Created                                         │
│      filter: bucket=raw, key prefix=sample-domain/, suffix=.csv          │
│                                                                          │
│    Lambda (trigger_pipeline.py):                                         │
│      1. Nhận event từ EventBridge                                        │
│      2. Kiểm tra file có phải .csv không (bỏ qua .json, .parquet)       │
│      3. Extract: bucket, key, domain name                                │
│      4. Start Step Functions execution với context                        │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │ Start execution
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ ⑤ ORCHESTRATION: Step Functions State Machine                            │
│                                                                          │
│    ┌──────────┐     ┌──────────┐     ┌─────────┐                       │
│    │ Stage A  │────>│ Stage B  │────>│ Success │                       │
│    │ (Glue)   │     │ (Glue)   │     │         │                       │
│    └────┬─────┘     └────┬─────┘     └─────────┘                       │
│         │ fail           │ fail                                          │
│         ▼                ▼                                               │
│    ┌──────────────────────────┐                                          │
│    │        FAILED            │ → CloudWatch Metric → Alarm → SNS       │
│    └──────────────────────────┘                                          │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │ Chạy Glue jobs
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ ④ TRANSFORM: Glue ETL Jobs                                              │
│                                                                          │
│ ┌─ Stage A (Light Transform) ─────────────────────────────────────────┐ │
│ │  Input:  s3://raw/sample-domain/orders.csv                          │ │
│ │  Output: Iceberg table "orders_staging" trong staging bucket         │ │
│ │                                                                      │ │
│ │  Xử lý:                                                             │ │
│ │    1. Đọc CSV với schema enforcement (StructType định nghĩa sẵn)    │ │
│ │    2. Loại bỏ records trùng order_id (dedup)                        │ │
│ │    3. Lọc bỏ records có order_id = null                             │ │
│ │    4. Thêm cột ingested_at (timestamp khi nạp)                      │ │
│ │    5. Ghi ra Iceberg table format v2 (Parquet underlying)           │ │
│ └──────────────────────────────────────────────────────────────────────┘ │
│                                  │                                       │
│                                  ▼                                       │
│ ┌─ Stage B (Heavy Transform) ─────────────────────────────────────────┐ │
│ │  Input:  Iceberg table "orders_staging"                             │ │
│ │  Output: Iceberg table "sales_summary" trong curated bucket         │ │
│ │                                                                      │ │
│ │  Xử lý:                                                             │ │
│ │    1. Đọc từ staging table                                          │ │
│ │    2. GROUP BY (order_date, category, region)                        │ │
│ │    3. Tính: order_count, total_quantity, total_revenue,              │ │
│ │            avg_order_value, unique_customers                         │ │
│ │    4. Tính cumulative_revenue (window function theo category+region)│ │
│ │    5. Partition theo year(order_date)                                │ │
│ │    6. Ghi ra curated Iceberg table                                  │ │
│ └──────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │ Sau khi transform xong
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ ⑥ DATA QUALITY: Glue Data Quality + Alert Lambda                         │
│                                                                          │
│    DQDL Rules chạy trên output tables:                                   │
│      • ColumnExists "order_id", "total_amount", ...                      │
│      • IsComplete "order_id" (không null)                                │
│      • IsUnique "order_id" (không trùng)                                 │
│      • ColumnValues "total_amount" > 0                                   │
│      • ColumnValues "category" in ["Electronics", "Clothing", ...]       │
│      • RowCount > 0                                                      │
│      • Completeness "total_amount" >= 0.95                               │
│                                                                          │
│    Nếu FAIL:                                                             │
│      EventBridge event → Lambda (dq_alert.py) → SNS → Email/Slack       │
│      Message chứa: ruleset name, score, danh sách rules bị vi phạm      │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │ Data đã sạch, nằm trong curated zone
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ ⑧ ANALYTICS: Athena + QuickSight                                         │
│                                                                          │
│    Athena Workgroup (data-platform-{env}):                               │
│      • Engine v3 (hỗ trợ Iceberg native)                                │
│      • Giới hạn 10 GB scan/query (tránh bill shock)                     │
│      • Kết quả tự lưu S3, encrypt, xoá sau 30 ngày                     │
│                                                                          │
│    SQL Views sẵn có:                                                     │
│      • daily_revenue: doanh thu theo ngày                                │
│      • monthly_category_performance: theo tháng + category               │
│      • regional_performance: theo khu vực                                │
│      • top_categories: top categories theo revenue                       │
│                                                                          │
│    QuickSight:                                                           │
│      • IAM role có quyền đọc curated + analytics buckets                │
│      • Kết nối Athena để tạo dashboards                                  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Luồng xử lý End-to-End (Streaming)

```
┌────────────────────┐
│  Application/IoT   │
│  (gửi events)      │
└─────────┬──────────┘
          │ PUT record
          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ ⑦ STREAMING: Kinesis Data Stream (on-demand)                             │
│    • Tự động scale theo traffic                                          │
│    • Không cần provision shards                                          │
│    • Lưu records 24h (có thể replay)                                    │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │ Batch: 100 records hoặc 60 giây
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ ⑦ STREAMING: Lambda Processor (stream_processor.py)                      │
│                                                                          │
│    1. Nhận batch records từ Kinesis                                      │
│    2. Decode base64 mỗi record                                          │
│    3. Validate JSON (skip invalid, không fail cả batch)                  │
│    4. Thêm metadata: _ingested_at, _partition_id                        │
│    5. Ghi JSON Lines vào S3 raw zone:                                    │
│       streaming-events/year=2024/month=08/day=22/hour=14/batch_xxx.json  │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │ File nằm trong S3 raw
                                  ▼
                    (Tiếp tục qua Batch flow: EventBridge → Lambda
                     → Step Functions → Glue → Curated → Athena)
```

---

## Các Scenario cụ thể

### Scenario 1: Team mới muốn onboard data lên platform

**Vấn đề:** Team Marketing muốn đưa campaign data lên platform nhưng không biết bắt đầu từ đâu.

**Giải pháp:**

```bash
# 1. Chạy 1 lệnh duy nhất
python domains/domain-template/onboard.py \
  --domain marketing \
  --owner marketing-team@company.com \
  --dataset campaigns

# 2. Script tự động tạo:
domains/marketing/
├── config.yaml                    # Cấu hình pipeline (schedule, workers)
├── transforms/stage_a/main.py     # Boilerplate code sẵn sàng chạy
├── transforms/stage_b/            # Team tự viết business logic
├── data_quality/                  # Định nghĩa DQ rules
├── athena/                        # SQL views
└── data/                          # Sample data

# 3. Team chỉ cần:
#    - Sửa stage_b/main.py cho logic nghiệp vụ riêng
#    - Thêm DQ rules
#    - Commit + push → CI/CD tự deploy
```

**Thời gian:** 5 phút (thay vì 1-2 tuần setup thủ công)

---

### Scenario 2: File CSV mới được upload → tự động xử lý

**Vấn đề:** Hệ thống source export CSV hàng ngày, cần tự động nạp và xử lý.

**Giải pháp (hoàn toàn tự động, 0 bước thủ công):**

```
Thời điểm 07:00 - Hệ thống source export CSV
    │
    ▼
07:01 - Upload vào: s3://raw/sample-domain/orders/orders_20240822.csv
    │
    ▼ (S3 → EventBridge event "Object Created")
    │
07:01 - EventBridge Rule match (prefix=sample-domain/, suffix=.csv)
    │
    ▼
07:01 - Lambda trigger_pipeline.py khởi động
    │   → Kiểm tra: file .csv ✓
    │   → Start Step Functions execution
    │
    ▼
07:02 - Step Functions chạy Stage A (Glue job)
    │   → Đọc CSV, validate schema
    │   → Dedup theo order_id
    │   → Lọc null records
    │   → Ghi Iceberg table "orders_staging"
    │   → ⏱ ~3 phút (tuỳ data size)
    │
    ▼
07:05 - Step Functions chạy Stage B (Glue job)
    │   → Đọc từ orders_staging
    │   → Aggregate: daily sales by category/region
    │   → Tính cumulative revenue
    │   → Ghi Iceberg table "sales_summary"
    │   → ⏱ ~5 phút
    │
    ▼
07:10 - Pipeline SUCCESS
    │   → Data sẵn sàng query
    │
    ▼
07:10 - User query qua Athena:
        SELECT category, SUM(total_revenue)
        FROM sales_summary
        WHERE year = 2024 AND month = 8
        GROUP BY category
        ORDER BY 2 DESC
```

---

### Scenario 3: Data quality check thất bại

**Vấn đề:** Ai đó upload CSV thiếu cột `total_amount`, hoặc có giá trị âm.

**Giải pháp:**

```
07:05 - Stage A transform xong, Glue DQ rules chạy trên orders_staging
    │
    │   Rules kiểm tra:
    │     ✓ ColumnExists "order_id"
    │     ✓ IsComplete "order_id"
    │     ✗ ColumnValues "total_amount" > 0    ← FAIL (có giá trị -5)
    │     ✗ Completeness "total_amount" >= 0.95 ← FAIL (chỉ 80%)
    │
    ▼
07:05 - Glue DQ phát event: state=FAILED, score=0.75
    │
    ▼ (EventBridge rule match: source=aws.glue-dataquality, state=FAILED)
    │
07:05 - Lambda dq_alert.py xử lý:
    │   → Parse event: ruleset="orders_staging_rules", score=75%
    │   → Lấy danh sách failed rules
    │   → Format message dễ đọc
    │
    ▼
07:05 - SNS publish → Email/Slack:
        ┌────────────────────────────────────────────────┐
        │ Subject: [Data Quality FAILED] orders_staging  │
        │                                                │
        │ Data Quality Check Failed                      │
        │ ========================================       │
        │ Ruleset: orders_staging_rules                  │
        │ State: FAILED                                  │
        │ Score: 75.0%                                   │
        │                                                │
        │ Failed Rules (2):                              │
        │   - ColumnValues "total_amount" > 0            │
        │   - Completeness "total_amount" >= 0.95        │
        └────────────────────────────────────────────────┘

HÀNH ĐỘNG CỦA TEAM:
  1. Nhận alert, kiểm tra source data
  2. Phát hiện: source system export sai format
  3. Fix tại source, re-upload CSV
  4. Pipeline tự chạy lại → DQ pass → data vào curated
```

---

### Scenario 4: Pipeline fail giữa chừng

**Vấn đề:** Stage A chạy xong nhưng Stage B lỗi (ví dụ: out of memory).

**Giải pháp:**

```
07:02 - Stage A SUCCESS ✓
    │
    ▼
07:05 - Stage B FAILED ✗ (error: OutOfMemoryError)
    │
    ▼
Step Functions → trạng thái FAILED (Stage B có catch → Fail state)
    │
    │ (KHÔNG chạy tiếp bất kỳ step nào)
    │ (Data trong staging KHÔNG bị ảnh hưởng - Iceberg table vẫn ở version cũ)
    │
    ▼
CloudWatch Metric: ExecutionsFailed = 1
    │
    ▼
CloudWatch Alarm trigger (threshold ≥ 1)
    │
    ▼
SNS → Email/Slack: "Pipeline data-platform-pipeline-prod FAILED"

HÀNH ĐỘNG CỦA TEAM:
  1. Nhận alert
  2. Xem Step Functions console → thấy Stage B fail
  3. Xem CloudWatch Logs → "OutOfMemoryError"
  4. Fix: tăng workers từ 4 lên 10 trong config
     git checkout -b infra/increase-stage-b-workers
     # Sửa transform_stack.py hoặc prod.yaml
     git commit + push + PR + merge
  5. CDK Pipeline tự deploy config mới
  6. Re-run pipeline (manual hoặc đợi trigger tiếp theo)
```

---

### Scenario 5: Streaming real-time events

**Vấn đề:** Ứng dụng web cần gửi clickstream events liên tục, không thể đợi batch hàng ngày.

**Giải pháp:**

```python
# Application code gửi events vào Kinesis
import boto3, json

kinesis = boto3.client('kinesis')

# Mỗi khi user click
kinesis.put_record(
    StreamName='data-platform-events-prod',
    Data=json.dumps({
        'event_type': 'page_view',
        'user_id': 'u12345',
        'page': '/products/laptop',
        'timestamp': '2024-08-22T14:30:00Z'
    }),
    PartitionKey='u12345'
)
```

```
14:30:00 - Event gửi vào Kinesis stream
14:30:01 - 99 events nữa đến...
    │
    ▼ (Lambda trigger: batch_size=100 HOẶC max_batching_window=60s)
    │
14:30:02 - Lambda stream_processor.py xử lý batch 100 records:
    │   → Decode base64
    │   → Validate JSON (skip invalid)
    │   → Thêm _ingested_at, _partition_id
    │   → Ghi 1 file JSON Lines:
    │     s3://raw/streaming-events/year=2024/month=08/day=22/hour=14/
    │                               batch_20240822143002_abc12345.json
    │
    ▼
14:30:03 - Data nằm trong S3 raw zone, sẵn sàng cho batch pipeline
           (hoặc query trực tiếp qua Athena nếu tạo external table)

LATENCY: < 3 giây từ khi event phát sinh đến khi nằm trong S3
```

---

### Scenario 6: Deploy thay đổi infrastructure

**Vấn đề:** Cần tăng Glue workers cho production vì data tăng 3x.

**Giải pháp (CDK Pipelines tự động):**

```
Developer:
    git checkout -b infra/increase-prod-workers
    # Sửa number_of_workers: 4 → 10
    git commit -m "infra: tăng stage_b workers từ 4 lên 10 cho prod"
    git push origin infra/increase-prod-workers
    # Tạo Pull Request → main
        │
        ▼
CI trên branch (KHÔNG deploy):
    ✓ Unit tests pass
    ✓ Lint pass
    ✓ CDK synth pass (validate templates)
        │
        ▼
Reviewer approve → Merge vào main
        │
        ▼
CDK Pipeline trigger (FULL deploy):
    │
    ├─ Synth: generate CloudFormation templates
    │
    ├─ Self-mutation: pipeline tự update nếu pipeline code thay đổi
    │
    ├─ Deploy DEV:
    │   Pre: unit tests + lint
    │   Deploy: all 9 stacks (workers=2, không thay đổi cho dev)
    │   Post: integration tests
    │
    ├─ Deploy STAGING:
    │   Pre: data contract validation
    │   Deploy: all 9 stacks (workers=4)
    │   Post: smoke tests (verify Glue jobs tồn tại)
    │
    ├─ Manual Approval: ← Platform engineer review staging results
    │
    └─ Deploy PROD:
        Deploy: all 9 stacks (workers=10 ← thay đổi có hiệu lực)
        Post: verification (list Glue jobs, confirm config mới)

TOÀN BỘ QUÁ TRÌNH: ~30 phút, 0 bước thủ công sau khi merge
```

---

### Scenario 7: Rollback khi deploy lỗi

**Vấn đề:** Deploy mới gây lỗi trên production.

**Giải pháp (2 loại rollback):**

```
CAS 1: Infrastructure deploy fail (ví dụ: IAM policy sai syntax)

    CDK Pipeline deploy stack...
        │
        ▼
    CloudFormation detect: CREATE_FAILED / UPDATE_FAILED
        │
        ▼
    CloudFormation TỰ ĐỘNG ROLLBACK về state trước đó
        │
        ▼
    Pipeline status: FAILED → EventBridge → SNS alert
        │
        ▼
    Team nhận alert, fix code, push lại

    ⚡ KHÔNG CẦN LÀM GÌ - CloudFormation tự rollback
    ⚡ Production KHÔNG bị ảnh hưởng


CAS 2: Transform code bug (ví dụ: logic aggregation sai)

    # Code mới đã deploy, pipeline chạy ra kết quả sai
    # Nhưng data cũ vẫn an toàn (Iceberg versioning)

    # Rollback transform code:
    git revert abc1234    # Revert commit gây lỗi
    git push origin main  # Push revert

    # CDK Pipeline tự deploy lại code cũ vào S3 scripts bucket
    # Lần chạy pipeline tiếp theo sẽ dùng code đã revert

    ⚡ Data cũ KHÔNG bị mất (Iceberg time-travel)
    ⚡ Code cũ tự động deploy lại qua pipeline
```

---

### Scenario 8: Query data bằng Athena

**Vấn đề:** Business analyst muốn xem doanh thu theo category mà không cần nhờ engineer.

**Giải pháp:**

```sql
-- Mở Athena console, chọn workgroup "data-platform-prod"
-- Database: data_platform_prod

-- Query 1: Doanh thu hàng ngày
SELECT order_date, category, total_revenue, order_count
FROM sales_summary
WHERE year = 2024 AND month = 8
ORDER BY order_date DESC, total_revenue DESC;

-- Query 2: Top categories tháng này
SELECT category,
       SUM(total_revenue) as revenue,
       SUM(order_count) as orders,
       AVG(avg_order_value) as avg_value
FROM sales_summary
WHERE year = 2024 AND month = 8
GROUP BY category
ORDER BY revenue DESC;

-- Query 3: So sánh regions
SELECT region,
       SUM(total_revenue) as revenue,
       SUM(unique_customers) as customers
FROM sales_summary
WHERE year = 2024
GROUP BY region;

-- Giới hạn tự động: 10 GB scan/query (tránh bill shock)
-- Kết quả tự lưu S3, encrypt, xoá sau 30 ngày
```

---

## Sau khi deploy: Checklist vận hành

### Bước 1: Deploy lần đầu

```bash
# Bootstrap CDK (1 lần cho mỗi AWS account)
cdk bootstrap aws://123456789012/us-east-1

# Deploy CICD stack (1 lần, sau đó pipeline tự update)
cdk deploy DataPlatform-CICD --app "uv run python infrastructure/cdk/app.py"

# Push code lên CodeCommit → pipeline tự chạy
git remote add codecommit https://git-codecommit.us-east-1.amazonaws.com/v1/repos/data-platform
git push codecommit main
```

### Bước 2: Pipeline tự deploy tất cả

```
CDK Pipeline tự động:
  1. Synth → validate tất cả stacks
  2. Deploy Dev → 9 stacks (Storage, Governance, Transform, ...)
  3. Integration tests trên Dev
  4. Deploy Staging → 9 stacks
  5. Smoke tests trên Staging
  6. [Manual Approval]
  7. Deploy Prod → 9 stacks
```

### Bước 3: Verify sau deploy

```bash
# Kiểm tra S3 buckets đã tạo
aws s3 ls | grep data-platform

# Kiểm tra Glue jobs
aws glue get-jobs --query 'Jobs[].Name'

# Kiểm tra Step Functions
aws stepfunctions list-state-machines --query 'stateMachines[].name'

# Kiểm tra Kinesis stream
aws kinesis list-streams
```

### Bước 4: Test end-to-end

```bash
# Generate sample data
uv run python domains/sample-domain/data/generate_sample.py

# Upload vào S3 raw → pipeline tự trigger
aws s3 cp domains/sample-domain/data/orders.csv \
  s3://data-platform-raw-dev-123456789012/sample-domain/orders/

# Theo dõi Step Functions execution
aws stepfunctions list-executions \
  --state-machine-arn arn:aws:states:us-east-1:123456789012:stateMachine:data-platform-pipeline-dev

# Sau ~10 phút, query kết quả qua Athena
aws athena start-query-execution \
  --query-string "SELECT * FROM data_platform_dev.sales_summary LIMIT 10" \
  --work-group data-platform-dev
```

### Bước 5: Subscribe alerts

```bash
# Thêm email nhận alerts
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:123456789012:data-platform-alerts-prod \
  --protocol email \
  --notification-endpoint oncall@company.com
```

---

## Tổng hợp: Platform giải quyết gì?

| Trước | Sau (với Platform) |
|-------|-------------------|
| Upload data → không ai biết | Upload data → tự động xử lý trong 10 phút |
| Muốn query → nhờ engineer | Mở Athena → tự query SQL |
| Data sai → phát hiện khi báo cáo | Data sai → alert ngay, chặn trước curated |
| Deploy thủ công → hay lỗi | Merge PR → tự deploy 3 environments |
| Team mới → chờ 2 tuần setup | Chạy 1 lệnh → sẵn sàng trong 5 phút |
| Pipeline fail → không ai biết | Fail → alert ngay qua Email/Slack |
| Chỉ batch hàng ngày | Batch + streaming real-time (< 3s latency) |
| Rollback → panic | Rollback tự động (CloudFormation) hoặc git revert |
| Không biết ai sửa gì | Git history + Pipeline logs + CloudWatch |
| Costs tăng không kiểm soát | Serverless + Athena scan limit + lifecycle policies |
