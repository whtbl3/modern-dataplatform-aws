# Mô tả dự án cho CV

---

## Phiên bản ngắn (2-3 dòng, dùng trong CV)

> **Modern Data Platform on AWS**
>
> Thiết kế và triển khai nền tảng dữ liệu serverless trên AWS phục vụ nhiều team, xử lý cả batch và real-time. Sử dụng AWS CDK (Python), Glue ETL với Apache Iceberg, Kinesis streaming, Step Functions orchestration, và CDK Pipelines CI/CD tự động deploy qua 3 environments. Áp dụng DataOps, data mesh (domain ownership), data quality gates, và self-service onboarding.

---

## Phiên bản trung bình (cho CV chi tiết hoặc LinkedIn)

### Modern Data Platform on AWS

**Vai trò:** Data/Platform Engineer | **Công nghệ:** AWS CDK, Glue, Kinesis, Step Functions, Athena, Lake Formation

Thiết kế và triển khai end-to-end một nền tảng dữ liệu hiện đại trên AWS theo kiến trúc serverless, phục vụ nhiều data domains (teams) với khả năng self-service.

**Thành tựu chính:**
- Xây dựng data lake 4 zones (raw → staging → curated → analytics) với Apache Iceberg table format, hỗ trợ time-travel và schema evolution
- Triển khai ETL pipeline 2 giai đoạn (SDLF pattern): Stage A (ingestion + validation + dedup) và Stage B (business logic + aggregation) sử dụng AWS Glue PySpark
- Thiết kế event-driven architecture: S3 → EventBridge → Lambda → Step Functions, tự động trigger pipeline khi có data mới (zero manual intervention)
- Xây dựng streaming pipeline (Kinesis → Lambda → S3) xử lý real-time events với latency < 3 giây
- Triển khai data quality automation: DQDL rules kiểm tra sau mỗi transform, tự động alert qua SNS khi vi phạm
- Implement CI/CD bằng CDK Pipelines (self-mutating): 1 pipeline duy nhất tự deploy qua Dev → Staging → Prod với testing gates ở mỗi stage
- Thiết kế self-service onboarding: team mới tự tạo domain trong 5 phút (thay vì 1-2 tuần setup thủ công)
- Áp dụng Lake Formation cho fine-grained access control (column-level security)
- Infrastructure as Code 100%: 10 CDK stacks, 0 resource tạo thủ công

**Công nghệ & Services:**
- **Compute:** AWS Glue (PySpark), Lambda (Python 3.12)
- **Storage:** S3, Apache Iceberg
- **Orchestration:** Step Functions, EventBridge
- **Streaming:** Kinesis Data Streams (on-demand)
- **Analytics:** Athena (engine v3), QuickSight
- **Governance:** Lake Formation, Glue Data Catalog, Macie
- **CI/CD:** CDK Pipelines, CodeCommit, CodeBuild, CodePipeline
- **Monitoring:** CloudWatch (dashboards + alarms), SNS
- **IaC:** AWS CDK (Python), CloudFormation

---

## Phiên bản đầy đủ (cho portfolio, phỏng vấn, hoặc case study)

### Bối cảnh & Vấn đề

Tổ chức có nhiều team (Sales, Marketing, Finance) nhưng:
- Dữ liệu phân tán ở nhiều hệ thống, không có nơi tập trung
- Quy trình xử lý thủ công, dễ lỗi, không reproducible
- Không kiểm soát chất lượng dữ liệu — lỗi chỉ phát hiện khi báo cáo sai
- Team mới muốn dùng data phải chờ hàng tuần để được setup
- Chi phí tăng không kiểm soát, không có cost governance

### Giải pháp

Thiết kế và triển khai Modern Data Platform theo các nguyên tắc:
- **Serverless-first:** Chỉ trả phí khi sử dụng, tự động scale
- **Domain ownership (Data Mesh):** Mỗi team sở hữu pipeline riêng
- **DataOps:** Automation, CI/CD, testing gates, observability
- **Self-service:** Team tự onboard, tự query, không cần ticket

### Kiến trúc

```
10 CDK Stacks triển khai:
  Storage → Governance → Transform → Orchestration → Monitoring
  → Ingestion → DataQuality → Streaming → Analytics → CICD
```

- **Data Lake Architecture:** 4 zones (raw/staging/curated/analytics) trên S3 với Iceberg format
- **ETL Pattern:** SDLF (Serverless Data Lake Framework) — Stage A (light) + Stage B (heavy)
- **Event-Driven:** EventBridge làm event bus trung tâm, Lambda làm glue code
- **Multi-Environment:** 1 codebase, 3 environments (dev/staging/prod) qua CDK Pipelines

### Kết quả đạt được

| Metric | Trước | Sau |
|--------|-------|-----|
| Thời gian từ data upload → sẵn sàng query | Hàng giờ (thủ công) | ~10 phút (tự động) |
| Onboard team mới | 1-2 tuần | 5 phút |
| Deploy thay đổi | Thủ công, hay lỗi | Tự động, 0 bước manual |
| Phát hiện data quality issue | Khi user báo | Real-time alert |
| Streaming latency | Không hỗ trợ | < 3 giây |
| Infrastructure reproducibility | Không | 100% IaC, deploy lại bất cứ lúc nào |
| Rollback capability | Panic, fix forward | Tự động (CloudFormation) hoặc git revert |

### Chi tiết kỹ thuật (dùng khi phỏng vấn)

**1. Tại sao chọn Iceberg thay vì Parquet/Hive?**
- ACID transactions: ghi song song không corrupt data
- Time-travel: query version cũ, rollback khi transform sai
- Schema evolution: thêm/đổi cột không cần rewrite toàn bộ data
- Hidden partitioning: user query không cần biết partition structure

**2. Tại sao dùng EventBridge thay vì S3 Notifications trực tiếp?**
- Tránh dependency cycle giữa Storage stack và Ingestion stack
- EventBridge cho phép filter phức tạp (prefix + suffix + bucket name)
- Dễ mở rộng: thêm rules mới không cần sửa S3 bucket config
- Content-based routing: khác nhau prefix → khác nhau pipeline

**3. Tại sao CDK Pipelines thay vì GitHub Actions / Jenkins?**
- Self-mutating: pipeline tự update khi code pipeline thay đổi
- Native AWS integration: không cần manage credentials cho deploy
- Immutable artifacts: synth 1 lần, deploy cùng artifact vào mọi env
- Built-in rollback: CloudFormation tự rollback khi fail

**4. Tại sao Step Functions thay vì Airflow / Glue Workflows?**
- Serverless: không cần maintain Airflow cluster
- Visual debugging: console hiển thị rõ step nào fail, input/output
- Built-in error handling: catch, retry, timeout ở mỗi step
- Pay-per-execution: không trả phí khi idle (Airflow chạy 24/7)

**5. Tại sao tách 10 stacks thay vì 1 stack lớn?**
- Deploy independence: update monitoring không cần deploy lại storage
- Blast radius nhỏ: lỗi 1 stack không ảnh hưởng stack khác
- Team ownership: team khác nhau có thể own stacks khác nhau
- CloudFormation limits: 1 stack tối đa 500 resources

**6. Data Quality approach:**
- DQDL (declarative rules) thay vì custom code → dễ maintain
- Chạy SAU transform (không chặn ingestion) → data vẫn vào raw
- Alert-based (không block pipeline) → team tự quyết định action
- Rules version-controlled cùng code → review qua PR

**7. Cost optimization:**
- Athena: 10 GB scan limit/query (tránh bill shock)
- Glue: on-demand workers, tắt khi xong
- Kinesis: on-demand mode (không cần provision shards)
- S3: lifecycle policies (xoá results sau 30 ngày)
- Lambda: 128-256 MB memory (đủ cho lightweight tasks)

---

## Các keywords cho ATS (Applicant Tracking System)

```
AWS, Amazon Web Services, Data Platform, Data Lake, Data Engineering,
AWS CDK, Infrastructure as Code, IaC, CloudFormation,
AWS Glue, PySpark, Apache Spark, ETL, ELT,
Apache Iceberg, Parquet, Data Lake Format,
Amazon S3, Amazon Kinesis, Streaming, Real-time,
AWS Step Functions, Orchestration, Workflow,
Amazon Athena, SQL, Query Engine, Serverless,
AWS Lake Formation, Data Governance, Access Control,
Amazon EventBridge, Event-Driven Architecture,
AWS Lambda, Serverless Computing, Python,
CI/CD, CDK Pipelines, CodePipeline, CodeBuild, DevOps, DataOps,
Data Quality, DQDL, Data Validation,
CloudWatch, Monitoring, Observability, Alerting,
Amazon QuickSight, BI, Business Intelligence,
Data Mesh, Domain-Driven Design, Self-Service,
SDLF, Serverless Data Lake Framework,
GitHub Flow, Git, Version Control,
Multi-Environment, Dev/Staging/Prod,
Cost Optimization, Serverless Architecture,
Python 3.12, pytest, Unit Testing
```

---

## Business Problem & Use Case: E-commerce Sales Analytics

### Bối cảnh doanh nghiệp

Một công ty e-commerce đang tăng trưởng nhanh:
- **200,000+ đơn hàng/tháng** từ website và mobile app
- **5 category sản phẩm:** Electronics, Clothing, Home & Garden, Sports, Books
- **4 khu vực:** US-East, US-West, EU-West, AP-Southeast
- **4 phương thức thanh toán:** Credit card, Debit card, PayPal, Bank transfer
- **3 teams** cần dùng data: Business (CEO, Finance), Marketing, Operations

### Vấn đề kinh doanh cụ thể

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    TRƯỚC KHI CÓ PLATFORM                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  CEO hỏi: "Doanh thu tuần này so với tuần trước thế nào?"                   │
│    → Data Analyst: "Để tôi export từ database, chạy Excel... 2-3 ngày"      │
│                                                                              │
│  Marketing hỏi: "Category nào đang trending để chạy campaign?"              │
│    → Engineer: "Để tôi viết query... à mà data format khác rồi, 1 tuần"    │
│                                                                              │
│  Operations hỏi: "Khu vực nào đang giảm đơn hàng?"                         │
│    → "Không ai biết cho đến khi báo cáo cuối tháng"                         │
│                                                                              │
│  Finance hỏi: "Tổng revenue Q3 chia theo payment method?"                   │
│    → "Export 3 file từ 3 hệ thống, merge thủ công, sai số ±5%"             │
│                                                                              │
│  ❌ 3-5 ngày để có 1 con số                                                 │
│  ❌ Mỗi lần hỏi lại phải làm lại từ đầu                                    │
│  ❌ Không ai tin số liệu vì mỗi team tính khác nhau                        │
│  ❌ Engineer mất 60% thời gian chạy query ad-hoc thay vì build product     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7 câu hỏi kinh doanh mà platform trả lời

| # | Câu hỏi | Ai cần | Tần suất | Trước (không có platform) | Sau (có platform) |
|---|---------|--------|----------|---------------------------|-------------------|
| 1 | Doanh thu hôm nay bao nhiêu? | CEO | Hàng ngày | 2-3 ngày (thủ công) | 30 giây (Athena query) |
| 2 | Category nào bán chạy nhất tháng này? | Marketing | Hàng tuần | 1 tuần (nhờ engineer) | Self-service dashboard |
| 3 | Khu vực nào đang giảm doanh thu? | Operations | Hàng ngày | Cuối tháng mới biết | Alert tự động khi giảm |
| 4 | Có đơn hàng bị duplicate không? | Engineering | Mỗi lần ingest | Không biết | Tự dedup + DQ check |
| 5 | Giá trị đơn trung bình theo category? | Finance | Hàng tháng | Export Excel, tính tay | Athena view sẵn có |
| 6 | Bao nhiêu khách unique mỗi ngày? | Product | Real-time | Không track được | unique_customers metric |
| 7 | Revenue tích luỹ theo thời gian? | Investors | Hàng quý | Accountant tổng hợp 2 tuần | cumulative_revenue tự tính |

### Giải pháp: Luồng data từ đơn hàng → insight

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SAU KHI CÓ PLATFORM                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────┐     orders.csv (hàng ngày từ source system)                │
│  │ Source      │     Mỗi record:                                            │
│  │ System      │       order_id, order_date, customer_id, category,         │
│  │ (POS/Web)   │       product_name, quantity, unit_price, total_amount,    │
│  └──────┬──────┘       region, payment_method                               │
│         │                                                                    │
│         │ Upload tự động vào S3 raw (hoặc manual lần đầu)                   │
│         ▼                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ STAGE A: Validation & Ingestion (~3 phút)                           │    │
│  │                                                                      │    │
│  │  ① Đọc CSV với schema enforcement                                   │    │
│  │     → Đảm bảo đúng 10 cột, đúng kiểu dữ liệu                      │    │
│  │     → Reject records thiếu order_id (không thể track)               │    │
│  │                                                                      │    │
│  │  ② Dedup theo order_id                                              │    │
│  │     → Loại đơn hàng bị gửi trùng (do retry, network issue)         │    │
│  │     → Tránh đếm doanh thu 2 lần cho cùng 1 đơn                     │    │
│  │                                                                      │    │
│  │  ③ Thêm metadata: ingested_at                                       │    │
│  │     → Biết data này được nạp khi nào (debug, audit)                 │    │
│  │                                                                      │    │
│  │  ④ Ghi ra Iceberg table "orders_staging"                            │    │
│  │     → Format chuẩn, có version history, query được ngay             │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│         │                                                                    │
│         ▼                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ DATA QUALITY CHECK                                                   │    │
│  │                                                                      │    │
│  │  ✓ ColumnValues "total_amount" > 0  (không cho đơn âm/zero)         │    │
│  │  ✓ ColumnValues "quantity" between 1 and 10000  (range hợp lý)      │    │
│  │  ✓ IsUnique "order_id"  (confirm dedup thành công)                  │    │
│  │  ✓ Completeness "total_amount" >= 0.95  (≤5% null chấp nhận được)  │    │
│  │  ✓ ColumnValues "category" in [5 categories]  (không có junk)       │    │
│  │  ✓ ColumnValues "region" in [4 regions]  (mapping đúng)            │    │
│  │                                                                      │    │
│  │  Nếu FAIL → SNS alert → Team biết ngay data source có vấn đề       │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│         │                                                                    │
│         ▼                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ STAGE B: Business Aggregation (~5 phút)                             │    │
│  │                                                                      │    │
│  │  ① GROUP BY (order_date, category, region)                          │    │
│  │     → Từ 200K đơn hàng → ~6000 summary records/tháng               │    │
│  │     → Query nhanh gấp 30x (scan ít data hơn)                       │    │
│  │                                                                      │    │
│  │  ② Tính metrics nghiệp vụ:                                          │    │
│  │     • order_count: số đơn hàng                                      │    │
│  │     • total_quantity: tổng số lượng sản phẩm                        │    │
│  │     • total_revenue: tổng doanh thu                                 │    │
│  │     • avg_order_value: giá trị đơn trung bình                       │    │
│  │     • unique_customers: số khách hàng unique                        │    │
│  │                                                                      │    │
│  │  ③ Tính cumulative_revenue (running total theo category+region)     │    │
│  │     → Investors xem growth trajectory không cần tính thêm           │    │
│  │                                                                      │    │
│  │  ④ Partition theo year(order_date)                                   │    │
│  │     → Query "doanh thu tháng 8" chỉ scan data tháng 8              │    │
│  │     → Tiết kiệm 90% Athena scan cost                               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│         │                                                                    │
│         ▼                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ ANALYTICS: Athena Views (query ngay, không cần code)                │    │
│  │                                                                      │    │
│  │  • daily_revenue:                                                    │    │
│  │      "Doanh thu mỗi ngày, breakdown theo category"                  │    │
│  │                                                                      │    │
│  │  • monthly_category_performance:                                     │    │
│  │      "So sánh categories theo tháng, tính MoM growth %"             │    │
│  │                                                                      │    │
│  │  • regional_performance:                                             │    │
│  │      "Revenue + order count + AOV theo khu vực"                      │    │
│  │                                                                      │    │
│  │  • top_categories:                                                   │    │
│  │      "Top 5 categories theo revenue, sorted descending"              │    │
│  │                                                                      │    │
│  │  CEO/Marketing/Finance: Mở Athena → chọn view → có kết quả         │    │
│  │  QuickSight: Connect Athena → Dashboard tự refresh hàng ngày        │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Streaming: Real-time user events từ website/app

```
Khi user thao tác trên website/app, events gửi vào Kinesis:

  {
    "event_type": "purchase",
    "user_id": "CUST-00142",
    "product": "Electronics_Product_12",
    "amount": 299.99,
    "region": "ap-southeast",
    "timestamp": "2024-08-22T14:30:00Z"
  }

Flow:
  App → Kinesis (on-demand, auto-scale) → Lambda (batch 100 records / 60s)
      → S3 raw zone (time-partitioned JSON Lines)
      → Tiếp tục vào batch pipeline (Glue Stage A → B → Athena)

Business value:
  • Marketing biết ngay campaign đang chạy có tăng purchase events không
  • Operations detect: nếu 0 purchase trong 30 phút → có thể website down
  • Product: xem real-time page_view nào popular nhất (A/B testing)
```

### Cụ thể: Các queries mà business teams chạy hàng ngày

```sql
-- CEO mỗi sáng: "Hôm qua bán được bao nhiêu?"
SELECT order_date, SUM(total_revenue) as revenue,
       SUM(order_count) as orders,
       SUM(unique_customers) as customers
FROM sales_summary
WHERE order_date = DATE '2024-08-21'
GROUP BY order_date;

-- Marketing hàng tuần: "Category nào đang tăng/giảm?"
SELECT category,
       SUM(CASE WHEN order_date BETWEEN DATE '2024-08-12' AND DATE '2024-08-18'
           THEN total_revenue END) as this_week,
       SUM(CASE WHEN order_date BETWEEN DATE '2024-08-05' AND DATE '2024-08-11'
           THEN total_revenue END) as last_week
FROM sales_summary
GROUP BY category
ORDER BY this_week DESC;

-- Operations: "Khu vực nào đang underperform?"
SELECT region,
       SUM(total_revenue) as revenue,
       SUM(order_count) as orders,
       AVG(avg_order_value) as aov
FROM sales_summary
WHERE year = 2024 AND month = 8
GROUP BY region
ORDER BY revenue ASC;  -- worst first

-- Finance cuối quý: "Revenue tích luỹ Q3?"
SELECT category, region,
       MAX(cumulative_revenue) as q3_total
FROM sales_summary
WHERE order_date BETWEEN DATE '2024-07-01' AND DATE '2024-09-30'
GROUP BY category, region
ORDER BY q3_total DESC;

-- Product: "Giá trị đơn trung bình đang tăng hay giảm?"
SELECT order_date, AVG(avg_order_value) as daily_aov
FROM sales_summary
WHERE order_date >= CURRENT_DATE - INTERVAL '30' DAY
ORDER BY order_date;
```

### Impact đo lường được

| Metric | Trước | Sau | Cải thiện |
|--------|-------|-----|-----------|
| Thời gian trả lời câu hỏi business | 2-5 ngày | 30 giây | **~1000x nhanh hơn** |
| Tần suất báo cáo doanh thu | Cuối tháng | Hàng ngày (tự động) | **30x thường xuyên hơn** |
| Phát hiện data anomaly | Khi user phàn nàn | Real-time alert | **Từ reactive → proactive** |
| Engineering time cho ad-hoc queries | 60% workload | ~0% (self-service) | **Giải phóng engineer** |
| Độ tin cậy số liệu | Mỗi team tính khác | Single source of truth | **1 con số duy nhất** |
| Thời gian onboard team analytics mới | 1-2 tuần | 5 phút | **~200x nhanh hơn** |
| Chi phí infrastructure khi idle | Server chạy 24/7 | $0 (serverless) | **Pay-per-use** |
| Khả năng rollback khi data sai | Không | Iceberg time-travel | **Zero data loss** |

### Timeline thực tế: 1 ngày hoạt động của platform

```
06:00 UTC  Source system export orders_20240822.csv (15,000 records)
06:01      Upload tự động vào s3://raw/sample-domain/orders/
06:01      EventBridge detect → Lambda trigger → Step Functions start
06:02      Stage A: validate + dedup → 14,850 valid records (150 duplicate loại)
06:05      Data Quality: 12/12 rules PASS ✓
06:05      Stage B: aggregate → 420 summary records (7 days × 5 categories × 4 regions × 3...)
06:10      Pipeline SUCCESS → Data sẵn sàng trong Athena

07:00      CEO mở QuickSight dashboard → thấy doanh thu hôm qua updated
09:00      Marketing query Athena: "Electronics tăng 15% WoW" → quyết định tăng ad spend
11:00      Operations nhận alert: "Region EU-West giảm 25% so với tuần trước"
           → Kiểm tra: warehouse EU có delay shipping → escalate logistics team
14:00      Streaming: 3,000 clickstream events/giờ → Kinesis → S3
           → Marketing monitor real-time: campaign mới launch đang tăng page_view
16:00      Finance query: "Revenue MTD = $2.3M, on-track cho target $3M"

TOÀN BỘ TỰ ĐỘNG. KHÔNG CẦN ENGINEER CAN THIỆP.
```

### Khi nào KHÔNG nên dùng platform này?

| Tình huống | Lý do | Giải pháp thay thế |
|-----------|-------|---------------------|
| < 1,000 đơn/tháng, 1 team | Over-engineering | S3 + Athena trực tiếp, không cần pipeline |
| Cần hiển thị doanh thu < 1 giây | Glue batch mất phút | DynamoDB + Lambda API |
| Đã có Snowflake/BigQuery | Không cần build từ đầu | Dùng tool có sẵn + dbt |
| Không có engineer AWS | Platform cần maintain | SaaS: Fivetran + dbt + Looker |
| Chỉ cần 1 báo cáo duy nhất | Pipeline overkill | Athena trực tiếp trên CSV |

---

## Tips khi nói về project trong phỏng vấn

1. **Bắt đầu bằng vấn đề, không phải giải pháp:**
   "Tổ chức có nhiều team cần dùng data nhưng không có nơi tập trung, xử lý thủ công, và không kiểm soát chất lượng..."

2. **Nêu quyết định và lý do (trade-offs):**
   "Tôi chọn Step Functions thay vì Airflow vì serverless — không cần maintain cluster, pay-per-execution, và visual debugging giúp team non-technical cũng hiểu flow"

3. **Đưa ra số liệu cụ thể:**
   "Giảm thời gian onboard team mới từ 2 tuần xuống 5 phút"
   "Pipeline end-to-end chạy trong ~10 phút, trước đó mất hàng giờ thủ công"

4. **Giải thích impact kinh doanh:**
   "Business analysts tự query data qua Athena mà không cần nhờ engineer, giải phóng engineering time cho tasks có giá trị cao hơn"

5. **Sẵn sàng đi sâu kỹ thuật:**
   - Giải thích dependency graph giữa 10 stacks
   - Giải thích cách tránh dependency cycle (EventBridge vs S3 notifications)
   - Giải thích self-mutating pipeline hoạt động ra sao
   - Giải thích Iceberg table format benefits cụ thể
