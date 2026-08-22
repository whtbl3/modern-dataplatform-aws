# Mô tả dự án cho CV

---

## Quá trình phát triển: Từ yêu cầu khách hàng → Production

### Tổng quan quy trình

```
┌────────────────────────────────────────────────────────────────────────────┐
│                 DATA PLATFORM DEVELOPMENT LIFECYCLE                          │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Phase 1          Phase 2           Phase 3          Phase 4               │
│  DISCOVERY        DESIGN            BUILD            OPERATE               │
│                                                                             │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐            │
│  │ Gather   │    │ Architect│    │ Implement│    │ Deploy & │            │
│  │ Require- │───>│ & Model  │───>│ & Test   │───>│ Monitor  │            │
│  │ ments    │    │          │    │          │    │          │            │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘            │
│                                                                             │
│  • Stakeholder    • 5V analysis    • IaC (CDK)     • CI/CD pipeline       │
│    interviews     • Tech selection • ETL code       • Observability        │
│  • Pain points    • Data modeling  • DQ rules       • Incident response    │
│  • SLA/NFR        • Architecture   • Unit tests     • Cost monitoring      │
│  • Data audit     • Trade-offs     • Integration    • Iterate              │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
```

---

### Phase 1: DISCOVERY — Thu thập & Phân tích yêu cầu

#### Bước 1.1: Stakeholder Interviews (Phỏng vấn các bên liên quan)

Gặp từng team để hiểu pain points thực tế:

| Stakeholder | Vai trò | Câu hỏi đặt ra | Pain point phát hiện |
|-------------|---------|-----------------|---------------------|
| CEO | Ra quyết định | "Khi nào ông cần xem doanh thu? Format nào?" | "Phải chờ 3 ngày, mỗi lần số khác nhau" |
| Head of Marketing | Lập campaign | "Làm sao biết category nào trending?" | "Nhờ engineer mất 1 tuần, data đã stale" |
| Operations Manager | Vận hành | "Phát hiện vấn đề khu vực thế nào?" | "Cuối tháng mới biết, đã mất revenue" |
| Finance Lead | Báo cáo tài chính | "Revenue report tạo ra sao?" | "3 nguồn, merge Excel, sai số 5%" |
| Data Engineer | Maintain pipeline | "Dành bao lâu cho ad-hoc queries?" | "60% thời gian, không build được gì mới" |
| New team (Analytics) | Muốn onboard | "Bao lâu để team mới dùng data?" | "2 tuần chờ setup, ticket qua IT" |

#### Bước 1.2: Requirements Documentation

**Functional Requirements (FR):**

| ID | Yêu cầu | Priority | Stakeholder |
|----|---------|----------|-------------|
| FR-1 | Tự động nạp data từ source (CSV) hàng ngày, không cần manual | Must | All |
| FR-2 | Loại bỏ duplicate, validate schema trước khi lưu | Must | Engineer, Finance |
| FR-3 | Aggregate doanh thu theo ngày/category/region | Must | CEO, Marketing |
| FR-4 | Business tự query bằng SQL, không cần engineer | Must | CEO, Marketing, Ops |
| FR-5 | Alert khi data quality fail | Should | Engineer, Ops |
| FR-6 | Streaming real-time cho clickstream events | Should | Marketing, Product |
| FR-7 | Team mới self-service onboard (< 1 ngày) | Should | Analytics team |
| FR-8 | Dashboard tự động refresh hàng ngày | Could | CEO, Marketing |

**Non-Functional Requirements (NFR):**

| ID | Yêu cầu | Target | Lý do |
|----|---------|--------|-------|
| NFR-1 | End-to-end latency (batch) | < 15 phút | CEO muốn xem data sáng hôm sau |
| NFR-2 | Streaming latency | < 5 giây | Real-time campaign monitoring |
| NFR-3 | Query response time | < 30 giây | Self-service phải nhanh |
| NFR-4 | Availability | 99.9% | Business-critical reporting |
| NFR-5 | Cost khi idle | ~$0 | Startup budget, trả khi dùng |
| NFR-6 | Data retention | 3+ năm | Regulatory + trend analysis |
| NFR-7 | Recovery (RPO/RTO) | RPO < 1 ngày, RTO < 1 giờ | Data không được mất |
| NFR-8 | Security | Encryption + access control | PII compliance |

#### Bước 1.3: Data Audit (Kiểm kê dữ liệu hiện tại)

```
Khảo sát: Dữ liệu nào đang có? Ở đâu? Format gì? Ai sở hữu?

┌─────────────────────────────────────────────────────────────────────┐
│ Data Source Inventory                                                │
├──────────────┬───────────┬─────────────┬──────────┬────────────────┤
│ Source       │ Format    │ Volume      │ Frequency│ Owner          │
├──────────────┼───────────┼─────────────┼──────────┼────────────────┤
│ POS system   │ CSV       │ 15K rows/day│ Daily    │ Operations     │
│ Website      │ JSON event│ 3K events/hr│ Real-time│ Engineering    │
│ Mobile app   │ JSON event│ 1K events/hr│ Real-time│ Engineering    │
│ CRM export   │ CSV       │ 5K rows/week│ Weekly   │ Sales          │
│ Payments     │ CSV       │ 15K rows/day│ Daily    │ Finance        │
└──────────────┴───────────┴─────────────┴──────────┴────────────────┘

Phát hiện:
  • POS data có ~1% duplicates (network retry)
  • Website events có ~3% invalid JSON (old client version)
  • Không có ai validate data quality hiện tại
  • Mỗi team export format khác nhau (date format, encoding)
```

#### Bước 1.4: Constraints & Assumptions

| Loại | Nội dung |
|------|----------|
| **Budget** | Startup stage → serverless (pay-per-use), không mua reserved capacity |
| **Team** | 1-2 data engineers, không có dedicated DevOps → cần automation cao |
| **Timeline** | MVP trong 4 tuần, full platform 8 tuần |
| **Cloud** | Đã dùng AWS cho application → stay in AWS ecosystem (tránh multi-cloud overhead) |
| **Skills** | Team biết Python, SQL. Không biết Scala/Java → chọn PySpark |
| **Compliance** | Encrypt at rest + transit. Chưa cần HIPAA/SOC2 nhưng prepare for future |

---

### Phase 2: DESIGN — Thiết kế kiến trúc

#### Bước 2.1: Phân tích 5V → Chọn Technology Stack

_(Chi tiết phần 5V analysis đã có phía dưới trong document)_

Tóm tắt quy trình tư duy:

```
Requirements        5V Analysis              Technology Decision
─────────────      ──────────────           ────────────────────

FR-1: Auto ingest  VELOCITY: batch 1/day    → EventBridge + Lambda trigger
                   + streaming 3K/hr        → Kinesis on-demand

FR-2: Dedup +      VERACITY: 1% duplicates  → Glue PySpark (dropDuplicates)
validate           + invalid ranges         → DQDL rules (declarative)

FR-3: Aggregate    VOLUME: 200K → 6K rows   → Glue Stage B (GROUP BY)
                   VARIETY: CSV in, SQL out  → Iceberg (unified format)

FR-4: Self-query   VALUE: 3 teams, ad-hoc   → Athena (SQL, serverless)
                   NFR-5: $0 khi idle       → pay-per-scan, not always-on

FR-6: Streaming    VELOCITY: 3K events/hr   → Kinesis (auto-scale)
                   NFR-2: < 5s latency      → Lambda micro-batch (60s window)

NFR-5: Cost ~$0    VOLUME: moderate         → Serverless everything
when idle          VELOCITY: bursty         → On-demand (Glue, Kinesis, Athena)
```

#### Bước 2.2: Architecture Design (High-Level)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    TARGET ARCHITECTURE                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  INGESTION        STORAGE         PROCESSING       SERVING          │
│  ──────────      ─────────       ────────────     ────────          │
│                                                                      │
│  EventBridge ──> S3 Raw     ──>  Glue ETL    ──> Athena            │
│  Lambda          (as-is)         (Stage A+B)      (SQL)            │
│  Kinesis         S3 Staging      Step Functions   QuickSight       │
│                  S3 Curated      (orchestrate)    (dashboard)       │
│                  S3 Analytics                                        │
│                                                                      │
│  GOVERNANCE       QUALITY          OBSERVABILITY    DEPLOYMENT      │
│  ──────────      ─────────        ──────────────   ────────────    │
│                                                                      │
│  Lake Formation  DQDL Rules       CloudWatch       CDK Pipelines   │
│  Glue Catalog    Alert Lambda     SNS Alerts       (self-mutating) │
│  Macie (PII)                      Dashboard        3 environments  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

#### Bước 2.3: Data Modeling

_(Chi tiết phần Data Model đã có phía dưới trong document)_

Quy trình chọn model:

```
Yêu cầu business                     Model decision
──────────────────                   ────────────────

"Query doanh thu theo category"  →   Cần aggregate table (không scan raw)
"Drill-down từng đơn hàng"      →   Cần giữ staging (transaction-level)
"Schema có thể thay đổi"        →   Cần Iceberg (schema evolution)
"Team nhỏ, ít dimensions"       →   Simplified star (không cần dim tables)
"3 năm historical data"         →   Partition by year (scan 1/3)
"Revenue tích luỹ cho investor" →   Pre-compute cumulative (window func)
```

#### Bước 2.4: Trade-off Decisions Log

| Quyết định | Lựa chọn A | Lựa chọn B | Chọn | Lý do |
|-----------|------------|------------|------|-------|
| ETL engine | Glue (PySpark) | Lambda (pandas) | Glue | 200K rows cần distributed processing, Lambda timeout 15m |
| Orchestration | Step Functions | Airflow (MWAA) | Step Functions | Serverless, $0 idle, team nhỏ không muốn maintain |
| Table format | Iceberg | Delta Lake | Iceberg | AWS native support tốt hơn, Glue + Athena integrate sẵn |
| CI/CD | CDK Pipelines | GitHub Actions | CDK Pipelines | Self-mutating, native AWS, immutable artifacts |
| Streaming | Kinesis | MSK (Kafka) | Kinesis | 3K events/hr quá nhỏ cho Kafka, Kinesis on-demand rẻ hơn |
| Query engine | Athena | Redshift Serverless | Athena | Pay-per-scan phù hợp budget, ad-hoc pattern |
| DQ approach | DQDL declarative | Custom Python | DQDL | Dễ maintain, domain team tự viết, version-controlled |
| Deploy model | Multi-account | Single-account multi-env | Single-account | Đơn giản cho MVP, migrate sang multi-account sau |

---

### Phase 3: BUILD — Triển khai & Kiểm thử

#### Bước 3.1: Infrastructure as Code

```
Tư duy tách stacks:

  "Mỗi stack = 1 nhóm resources có lifecycle chung"

  ┌────────────────────────────────────────────────────┐
  │ Stack decomposition logic:                          │
  │                                                     │
  │ Q: Khi nào deploy cùng nhau?                       │
  │ A: S3 buckets + IAM role → STORAGE stack            │
  │                                                     │
  │ Q: Ai depend vào ai?                               │
  │ A: Transform cần Storage → Transform depends on     │
  │    Storage, nhưng Monitoring độc lập                │
  │                                                     │
  │ Q: Team nào own?                                    │
  │ A: Platform team: Storage, CICD, Monitoring         │
  │    Domain team: Transform, DataQuality              │
  │                                                     │
  │ Q: Blast radius?                                    │
  │ A: Sửa alarm không nên risk break S3 bucket        │
  │    → Tách Monitoring riêng                          │
  └────────────────────────────────────────────────────┘

  Kết quả: 10 stacks, dependency graph rõ ràng
```

#### Bước 3.2: ETL Development (Transform code)

```
Phát triển theo Test-Driven Data Pipeline:

  1. Viết DQ rules TRƯỚC (= acceptance criteria)
     "order_id phải unique, amount phải > 0"

  2. Viết unit tests cho logic transform
     test_dedup: 2 records cùng id → chỉ giữ 1
     test_null_filter: record thiếu id → loại bỏ
     test_aggregation: 3 records → sum đúng

  3. Implement Stage A + Stage B
     Stage A: validate → dedup → type cast → write Iceberg
     Stage B: read staging → GROUP BY → window func → write curated

  4. Integration test (chạy với data thật trên AWS)
     Upload sample CSV → verify pipeline end-to-end
```

#### Bước 3.3: Testing Strategy

```
                          ┌─────────────────────┐
                          │ Production          │ ← Chỉ code đã qua TẤT CẢ layers
                          └──────────┬──────────┘
                                     │
                          ┌──────────┴──────────┐
                          │ Smoke Tests         │ ← Services tồn tại và respond?
                          │ (post-staging)      │
                          └──────────┬──────────┘
                                     │
                          ┌──────────┴──────────┐
                          │ Integration Tests   │ ← Pipeline chạy end-to-end trên AWS?
                          │ (post-dev deploy)   │
                          └──────────┬──────────┘
                                     │
                          ┌──────────┴──────────┐
                          │ Data Contract Tests │ ← DQ rules vẫn valid?
                          │ (pre-staging)       │   Schema không bị break?
                          └──────────┬──────────┘
                                     │
                          ┌──────────┴──────────┐
                          │ Unit Tests          │ ← Logic đúng? Dedup OK?
                          │ (pre-deploy, mọi    │   Aggregation đúng?
                          │  commit)            │   25 tests, < 1 giây
                          └─────────────────────┘

Chi phí fix bug tăng dần theo layer → test nhiều ở dưới (shift-left)
```

#### Bước 3.4: Security Review

| Layer | Kiểm tra | Implementation |
|-------|---------|----------------|
| Storage | Data encrypted at rest? | S3 SSE-S3 (default encryption) |
| Storage | Public access blocked? | BlockPublicAccess.BLOCK_ALL |
| Network | Data encrypted in transit? | HTTPS only (S3, Glue, Athena) |
| IAM | Least privilege? | Mỗi service chỉ có quyền cần thiết |
| Governance | Ai đọc được data nào? | Lake Formation (table/column-level) |
| PII | Có data nhạy cảm không? | Macie scan raw + curated buckets |
| Secrets | Credentials trong code? | Environment variables, không hard-code |
| Audit | Ai làm gì khi nào? | CloudTrail + S3 access logging |

---

### Phase 4: OPERATE — Vận hành & Cải tiến

#### Bước 4.1: Deployment Pipeline

```
Code commit → CDK Pipelines tự động:

  ┌───────┐   ┌───────┐   ┌─────────┐   ┌─────────┐   ┌──────┐
  │ Synth │──>│  Dev  │──>│ Staging │──>│Approval │──>│ Prod │
  └───────┘   └───────┘   └─────────┘   └─────────┘   └──────┘
      │            │            │                           │
  Validate    Deploy +      Deploy +      Human         Deploy +
  all stacks  integration   smoke tests   review        verification
              tests
```

#### Bước 4.2: Observability & Alerting

| Metric | Alert condition | Action |
|--------|----------------|--------|
| Glue job failed | failures ≥ 1 trong 5 phút | SNS → Slack → Engineer on-call |
| Step Functions failed | failures ≥ 1 trong 5 phút | SNS → Slack → Engineer on-call |
| Data Quality failed | Bất kỳ rule nào FAIL | SNS → Domain team owner |
| Pipeline duration | > 30 phút (bình thường 10) | Investigate: data tăng? code chậm? |
| No data arrived | 0 files in 24h (expected daily) | Check source system |

#### Bước 4.3: Runbook (Quy trình xử lý sự cố)

```
Khi nhận alert "Pipeline FAILED":

  1. Xem Step Functions console → step nào fail?
  2. Xem CloudWatch Logs → error message cụ thể?
  3. Phân loại:
     a. Data issue (schema drift, bad data)
        → Fix tại source, re-upload, pipeline tự chạy lại
     b. Infrastructure issue (timeout, OOM)
        → Tăng workers/memory, deploy qua CDK Pipeline
     c. Code bug (logic sai)
        → Fix code, commit, CDK Pipeline tự deploy
        → Hoặc git revert nếu urgent

  4. Post-mortem: Cập nhật DQ rules để bắt issue này sớm hơn lần sau
```

#### Bước 4.4: Continuous Improvement

```
Sprint 1-2 (MVP):
  ✓ Batch pipeline: CSV → Iceberg → Athena
  ✓ Basic monitoring + alerts

Sprint 3-4:
  ✓ Streaming pipeline (Kinesis)
  ✓ Data Quality automation
  ✓ Self-service onboarding

Sprint 5-6:
  ✓ Cost optimization (partition, scan limits)
  ✓ Multi-environment CI/CD
  ✓ Dashboard (QuickSight)

Backlog (future):
  □ Multi-account deployment (AWS Organizations)
  □ DataZone catalog (business metadata)
  □ ML feature store trên curated data
  □ Real-time alerting (Kinesis → Lambda → SNS trực tiếp)
  □ Data lineage tracking
```

---

### Tóm tắt: Trả lời phỏng vấn theo framework

Khi interviewer hỏi "Giải thích quá trình bạn xây dựng platform này", trả lời theo 4 phases:

```
"Đầu tiên tôi gather requirements từ stakeholders — phỏng vấn CEO,
Marketing, Operations, Finance để hiểu pain points thực tế. Pain point
lớn nhất là phải chờ 3-5 ngày để có 1 con số doanh thu, và mỗi team
tính ra kết quả khác nhau.

Sau đó tôi phân tích đặc điểm data theo 5V framework để chọn công nghệ:
Volume moderate (200K records/tháng) → S3 + Glue (serverless, scale khi cần),
Velocity cần cả batch và streaming → EventBridge + Kinesis,
Variety nhiều format → Iceberg (schema evolution),
Veracity có duplicates + invalid data → DQDL rules + dedup pipeline,
Value cần self-service → Athena + QuickSight.

Về data model, tôi chọn simplified star schema: giữ staging table
(transaction-level, source of truth) và curated table (pre-aggregated,
optimized cho queries). Không tách dimension tables riêng vì chỉ có
5 categories + 4 regions — đơn giản hơn, query nhanh hơn trên Athena.

Build theo IaC 100% với AWS CDK, tách 10 stacks theo blast radius,
test-driven (unit tests trước, DQ rules = acceptance criteria),
deploy qua CDK Pipelines self-mutating.

Kết quả: thời gian từ data → insight giảm từ 3-5 ngày xuống 30 giây,
engineer không còn bị interrupt cho ad-hoc queries, phát hiện data
quality issues proactively thay vì khi user phàn nàn."
```

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

### Phân tích 5V → Quyết định chọn Technology Stack

Mọi quyết định công nghệ trong platform đều xuất phát từ phân tích đặc điểm dữ liệu theo mô hình **5V of Big Data**:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         5V ANALYSIS → TECHNOLOGY DECISIONS                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐     │
│  │ VOLUME  │   │VELOCITY │   │ VARIETY │   │VERACITY │   │  VALUE  │     │
│  │ Khối    │   │ Tốc độ  │   │ Đa dạng │   │Độ tin   │   │ Giá trị │     │
│  │ lượng   │   │         │   │         │   │ cậy     │   │         │     │
│  └────┬────┘   └────┬────┘   └────┬────┘   └────┬────┘   └────┬────┘     │
│       │              │              │              │              │          │
│       ▼              ▼              ▼              ▼              ▼          │
│   S3 + Glue     Kinesis +      Iceberg +     Data Quality   Athena +       │
│   (scale to     EventBridge    Glue ETL      (DQDL rules)   QuickSight     │
│    petabytes)   (real-time)    (any format)   (validate)    (self-service)  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### ① VOLUME (Khối lượng) → Chọn S3 + Glue + Athena

| Đặc điểm data | Con số cụ thể | Yêu cầu | Giải pháp |
|---------------|---------------|----------|-----------|
| Đơn hàng/tháng | 200,000+ records | Lưu trữ lâu dài, rẻ | S3 ($0.023/GB/tháng) |
| Tăng trưởng | ~30% YoY | Scale không cần re-architect | S3 unlimited + Glue auto-scale workers |
| Lịch sử | Giữ 3+ năm | Query historical data | Iceberg partition by year (scan ít) |
| Aggregate output | ~6,000 records/tháng | Query nhanh | Athena scan ~MB thay vì GB |

**Tại sao KHÔNG chọn:**
- ❌ RDS/PostgreSQL: giới hạn vài TB, scale vertical đắt, không partition tốt cho analytics
- ❌ DynamoDB: tốt cho key-value lookup, tệ cho aggregate queries (full table scan)
- ❌ Redshift: tốt nhưng over-kill cho volume này, có minimum cost kể cả khi idle

**Tại sao chọn S3 + Glue:**
- ✅ S3: unlimited storage, $0.023/GB, lifecycle policies tự xoá data cũ
- ✅ Glue: serverless Spark, chỉ trả khi chạy, auto-scale workers theo data size
- ✅ Athena: scan-based pricing ($5/TB scanned), partition pruning giảm cost 90%

#### ② VELOCITY (Tốc độ) → Chọn Kinesis + EventBridge + Lambda

| Đặc điểm | Con số | Yêu cầu | Giải pháp |
|-----------|--------|----------|-----------|
| Batch ingestion | 1 file/ngày (15K records) | Trigger pipeline tự động | EventBridge + Lambda |
| Streaming events | 3,000+ events/giờ (peak) | Latency < 5 giây | Kinesis on-demand |
| Processing window | 100 records hoặc 60 giây | Micro-batch hiệu quả | Lambda batch config |
| Pipeline E2E | Upload → query-ready | < 15 phút | Step Functions orchestration |

**Tại sao KHÔNG chọn:**
- ❌ Apache Kafka (MSK): cần manage cluster, overkill cho 3K events/giờ, tốn tiền khi idle
- ❌ SQS: không có replay, không có ordering guarantee, khó fan-out
- ❌ Cron job polling S3: delay cao (phút), miss files, không event-driven

**Tại sao chọn Kinesis + EventBridge:**
- ✅ Kinesis on-demand: auto-scale, không cần provision shards, replay 24h
- ✅ EventBridge: native S3 integration, content-based filtering, zero cost khi idle
- ✅ Lambda: cold start < 1s, pay-per-invocation, perfect cho lightweight trigger

#### ③ VARIETY (Đa dạng) → Chọn Iceberg + Glue ETL + 4-zone architecture

| Đặc điểm | Ví dụ cụ thể | Yêu cầu | Giải pháp |
|-----------|-------------|----------|-----------|
| Source formats | CSV, JSON, streaming JSON | Ingest bất kỳ format nào | S3 raw zone (schema-on-read) |
| Schema changes | Thêm cột "discount" tháng sau | Không break pipeline cũ | Iceberg schema evolution |
| Multiple domains | Sales, Marketing, Operations | Mỗi domain format khác | Domain-based folder structure |
| Output consumers | SQL analysts, BI tools, ML | 1 data phục vụ nhiều mục đích | Curated zone (Iceberg) + Athena |

**Tại sao KHÔNG chọn:**
- ❌ Single database (Redshift): buộc phải define schema trước, mỗi thay đổi = migration
- ❌ Plain Parquet trên S3: không có schema evolution, partition thay đổi = rewrite toàn bộ
- ❌ Delta Lake: tied vào Databricks ecosystem, Glue hỗ trợ Iceberg native tốt hơn

**Tại sao chọn Iceberg:**
- ✅ Schema evolution: thêm/đổi/xoá cột mà consumer cũ vẫn chạy
- ✅ Hidden partitioning: engine tự partition, user query không cần biết structure
- ✅ Time-travel: query version cũ khi transform mới bị lỗi
- ✅ ACID: multiple writers không corrupt data

#### ④ VERACITY (Độ tin cậy) → Chọn Glue Data Quality + Alert Lambda + Dedup

| Đặc điểm | Rủi ro nếu không xử lý | Yêu cầu | Giải pháp |
|-----------|------------------------|----------|-----------|
| Duplicate orders | Đếm doanh thu 2 lần | Dedup trước khi aggregate | Stage A: dropDuplicates("order_id") |
| Null values | Aggregate sai (NaN) | Loại bỏ hoặc default | Stage A: filter order_id NOT NULL |
| Invalid range | amount = -999 (lỗi source) | Reject records bất hợp lý | DQDL: ColumnValues "amount" > 0 |
| Wrong enum | category = "Elctronics" (typo) | Validate domain values | DQDL: ColumnValues "category" in [...] |
| Missing data | 50% records thiếu region | Phát hiện sớm, alert | DQDL: Completeness "region" >= 0.95 |
| Schema drift | Source thêm cột, đổi tên | Không crash pipeline | Iceberg schema evolution + Stage A enforce |

**Tại sao KHÔNG chọn:**
- ❌ Validate ở application layer: data đã vào lake rồi mới phát hiện lỗi
- ❌ Custom Python validation code: khó maintain, không declarative, mỗi domain viết khác
- ❌ Block pipeline khi DQ fail: data vẫn cần vào raw zone (source of truth), chỉ chặn ở curated

**Tại sao chọn DQDL + alert approach:**
- ✅ Declarative rules: dễ đọc, dễ review, domain team tự viết
- ✅ Chạy SAU Stage A: data luôn vào raw (không mất), DQ check trước curated
- ✅ Alert (không block): team tự đánh giá severity, quyết định action
- ✅ Version-controlled: rules nằm trong git, thay đổi qua PR review

#### ⑤ VALUE (Giá trị) → Chọn Athena + QuickSight + Self-service

| Đặc điểm | Business need | Yêu cầu | Giải pháp |
|-----------|-------------|----------|-----------|
| Ad-hoc queries | CEO hỏi bất kỳ lúc nào | Query không cần engineer | Athena (SQL tự phục vụ) |
| Dashboards | Marketing cần visual | Tự tạo/sửa dashboard | QuickSight connect Athena |
| Cost efficiency | Không query 24/7 | Chỉ trả khi dùng | Athena pay-per-scan + Glue pay-per-run |
| Time to insight | "Biết ngay, hành động ngay" | < 30 giây từ question → answer | Pre-aggregated views + Athena |
| Multi-team access | 3 teams dùng chung | Governance, không conflict | Lake Formation + domain isolation |

**Tại sao KHÔNG chọn:**
- ❌ Jupyter notebooks: cần code, không self-service cho business
- ❌ Redshift always-on: trả $0.25/giờ kể cả khi không ai query
- ❌ Export Excel hàng tháng: stale data, không interactive, không reproducible

**Tại sao chọn Athena + QuickSight:**
- ✅ Athena: $5/TB scanned, 0 cost khi idle, standard SQL, Iceberg native
- ✅ QuickSight: business tự tạo dashboard, auto-refresh, share trong org
- ✅ 10 GB scan limit: tự động chặn query quét quá nhiều (cost governance)
- ✅ Pre-built views: business không cần viết SQL phức tạp

#### Tổng hợp: 5V → Technology Map

```
┌──────────────┬──────────────────────────────┬────────────────────────────────┐
│      V       │     Thách thức cụ thể        │    Công nghệ đã chọn           │
├──────────────┼──────────────────────────────┼────────────────────────────────┤
│ VOLUME       │ 200K+ records/tháng,         │ S3 (storage) + Glue (compute) │
│              │ tăng 30% YoY, giữ 3 năm     │ + Athena (query)               │
├──────────────┼──────────────────────────────┼────────────────────────────────┤
│ VELOCITY     │ Batch hàng ngày +            │ EventBridge + Lambda (batch)   │
│              │ streaming 3K events/giờ      │ + Kinesis (streaming)          │
├──────────────┼──────────────────────────────┼────────────────────────────────┤
│ VARIETY      │ CSV + JSON + streaming,      │ Iceberg (unified format)       │
│              │ schema thay đổi theo thời    │ + 4-zone lake architecture     │
│              │ gian, nhiều domains          │ + Glue ETL (transform any)     │
├──────────────┼──────────────────────────────┼────────────────────────────────┤
│ VERACITY     │ Duplicates, nulls, invalid   │ Glue DQ (DQDL rules)          │
│              │ ranges, schema drift         │ + Stage A dedup/validate       │
│              │                              │ + SNS alerts                   │
├──────────────┼──────────────────────────────┼────────────────────────────────┤
│ VALUE        │ 3 teams cần insight nhanh,   │ Athena (self-service SQL)      │
│              │ tự phục vụ, cost-effective   │ + QuickSight (dashboards)      │
│              │                              │ + Pre-aggregated views         │
└──────────────┴──────────────────────────────┴────────────────────────────────┘
```

---

### Data Model: Tại sao chọn Star Schema trên Data Lake (Hybrid approach)

#### Các lựa chọn data model

| Model | Mô tả | Ưu điểm | Nhược điểm |
|-------|--------|---------|------------|
| **Flat denormalized** | 1 bảng chứa tất cả | Đơn giản, dễ query | Redundancy cao, scan nhiều |
| **Star schema** | Fact table + dimension tables | Query nhanh, dễ hiểu | Cần maintain dimensions |
| **Data Vault** | Hub + Satellite + Link | Audit trail, historized | Quá phức tạp cho 1 domain |
| **One Big Table (OBT)** | Pre-join tất cả vào 1 bảng | Cực nhanh cho BI | Không flexible khi thêm dimension |

#### Quyết định: Star Schema đơn giản hoá (2 layers)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DATA MODEL ARCHITECTURE                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  STAGING LAYER (orders_staging)          CURATED LAYER (sales_summary)       │
│  ─────────────────────────────          ──────────────────────────────      │
│  = Transaction-level detail              = Pre-aggregated fact table          │
│  = Source of truth (deduped)             = Optimized cho queries              │
│                                                                              │
│  ┌─────────────────────────┐            ┌─────────────────────────────┐     │
│  │  orders_staging         │            │  sales_summary              │     │
│  │  (Iceberg table)        │            │  (Iceberg table)            │     │
│  ├─────────────────────────┤            ├─────────────────────────────┤     │
│  │  order_id        PK     │            │  order_date         PK(1)  │     │
│  │  order_date             │──────┐     │  category           PK(2)  │     │
│  │  customer_id            │      │     │  region             PK(3)  │     │
│  │  category               │      │     ├─────────────────────────────┤     │
│  │  product_name           │      │     │  order_count        metric │     │
│  │  quantity               │      ├────>│  total_quantity     metric │     │
│  │  unit_price             │      │     │  total_revenue      metric │     │
│  │  total_amount           │      │     │  avg_order_value    metric │     │
│  │  region                 │      │     │  unique_customers   metric │     │
│  │  payment_method         │      │     │  cumulative_revenue metric │     │
│  │  ingested_at            │      │     ├─────────────────────────────┤     │
│  └─────────────────────────┘      │     │  year               part.  │     │
│                                    │     │  month              part.  │     │
│                                    │     │  processed_at       audit  │     │
│                 Stage B            │     └─────────────────────────────┘     │
│               (GROUP BY +          │                                         │
│                window func)        │     Partition: year(order_date)         │
│                                    │     Granularity: 1 row per              │
│                                    │       (date × category × region)       │
│                                    │                                         │
└────────────────────────────────────┴─────────────────────────────────────────┘
```

#### Tại sao chọn model này?

**1. Tại sao 2 layers thay vì 1?**

```
Nếu chỉ có orders_staging (raw detail):
  • Query "doanh thu theo category": scan 200K records → chậm, đắt
  • Mỗi query phải GROUP BY lại → duplicate compute
  • Business user phải viết SQL phức tạp

Với sales_summary (pre-aggregated):
  • Cùng query: scan 420 records (30 ngày × 5 cat × ~3 region) → 1000x ít hơn
  • Metrics tính sẵn → query chỉ cần SELECT + WHERE
  • Business user chọn Athena view → có kết quả ngay
```

**2. Tại sao Star Schema đơn giản hoá (không có dimension tables riêng)?**

```
Star Schema truyền thống:
  fact_sales ──→ dim_category (category_id, category_name, department)
             ──→ dim_region (region_id, region_name, country, timezone)
             ──→ dim_date (date_id, year, quarter, month, week, day_of_week)
             ──→ dim_customer (customer_id, segment, tier, registration_date)

Project này chọn SIMPLIFIED star:
  sales_summary chứa luôn category, region, date (không tách dimension)
```

| Lý do | Giải thích |
|-------|-----------|
| Số lượng dimensions ít | Chỉ 5 categories, 4 regions → không cần bảng riêng |
| Dimensions ít thay đổi | Category list cố định, region cố định |
| Query simplicity | JOIN giữa fact + dimensions tốn thêm latency trên Athena |
| Data lake ≠ Data warehouse | Athena tối ưu cho scan flat tables, không phải star join |
| Team size nhỏ | Không cần governance phức tạp cho dimension management |

**Khi nào CẦN tách dimension tables:**
- Khi category có 500+ giá trị và metadata phong phú (hierarchy, manager, budget)
- Khi cần SCD Type 2 (slowly changing dimensions) - ví dụ: customer đổi tier
- Khi nhiều fact tables cùng reference 1 dimension (reuse)

**3. Tại sao partition theo year(order_date)?**

```
Không partition:
  Query "doanh thu tháng 8/2024" → scan TOÀN BỘ bảng (3 năm data)
  Cost: $5/TB × toàn bộ data

Partition theo year:
  Query "doanh thu tháng 8/2024" → scan CHỈ partition year=2024
  Cost: $5/TB × 1/3 data = tiết kiệm 66%

Tại sao year thay vì month hoặc day?
  • month: quá nhiều partitions (36+ cho 3 năm) → overhead
  • day: 1000+ partitions → Glue Catalog chậm, small files problem
  • year: 3-4 partitions, mỗi partition đủ lớn (>128MB), scan cost hợp lý
```

**4. Tại sao giữ cả staging VÀ curated (không chỉ curated)?**

```
staging (orders_staging):
  • Source of truth: mọi record gốc (sau dedup) đều ở đây
  • Dùng khi: cần drill-down chi tiết 1 đơn hàng cụ thể
  • Dùng khi: Stage B logic thay đổi → chạy lại từ staging (không cần re-ingest)
  • Dùng khi: debug "tại sao doanh thu hôm qua giảm?" → xem từng order

curated (sales_summary):
  • Optimized cho analytics: pre-aggregated, partitioned
  • Dùng khi: dashboard daily/weekly/monthly
  • Dùng khi: business query ad-hoc (nhanh, rẻ)
  • 1000x ít records hơn staging → query nhanh hơn rất nhiều
```

**5. Tại sao có cumulative_revenue (window function)?**

```sql
-- Không có cumulative_revenue:
-- Business phải viết:
SELECT order_date, category, region,
       SUM(total_revenue) OVER (
         PARTITION BY category, region
         ORDER BY order_date
         ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
       ) as cumulative
FROM sales_summary;
-- → Phức tạp, dễ sai, mỗi lần query phải tính lại

-- Có cumulative_revenue (đã tính sẵn trong Stage B):
SELECT order_date, category, region, cumulative_revenue
FROM sales_summary
WHERE category = 'Electronics' AND region = 'us-east';
-- → Đơn giản, nhanh, business tự làm được
```

#### Data Flow qua các layers

```
┌──────────┐     ┌──────────────┐     ┌───────────────┐     ┌──────────────┐
│  RAW     │     │   STAGING    │     │   CURATED     │     │  ANALYTICS   │
│  (S3)    │────>│  (Iceberg)   │────>│   (Iceberg)   │────>│   (Views)    │
└──────────┘     └──────────────┘     └───────────────┘     └──────────────┘
                                                                     │
 orders.csv       orders_staging       sales_summary          Athena views
 (as-is from      (deduped,            (aggregated,           (pre-written
  source)          validated,            partitioned,           SQL cho
                   typed)                metrics sẵn)           business)

 Schema:          Schema:               Schema:               Output:
 Không enforce    Enforced              Business metrics      Kết quả trực tiếp
                  (StructType)          (đã tính toán)        (cho dashboard)

 Dùng bởi:       Dùng bởi:             Dùng bởi:            Dùng bởi:
 Không ai query  Data Engineer         Everyone              Business users
 trực tiếp       (debug, re-process)   (query, dashboard)    (QuickSight)
```

#### So sánh với các approach khác

| Approach | Khi nào phù hợp | Tại sao KHÔNG chọn cho project này |
|----------|-----------------|-----------------------------------|
| **Data Vault** | Enterprise với 100+ sources, cần full audit history, regulatory compliance nặng | Quá phức tạp cho 1 domain, team nhỏ, overhead maintain Hub/Sat/Link |
| **One Big Table** | BI team chỉ cần 1 bảng duy nhất, data ít thay đổi structure | Không flexible: thêm dimension = rebuild toàn bộ bảng |
| **Medallion (Bronze/Silver/Gold)** | Databricks ecosystem, nhiều layers transform | Tương tự 4-zone approach, nhưng naming khác (raw=bronze, staging=silver, curated=gold) |
| **Kimball Star Schema** | Data warehouse truyền thống (Redshift, Snowflake) | Athena không optimize cho multi-table joins, data lake favor flat/wide tables |
| **Activity Schema** | Event-driven analytics (Segment, Amplitude style) | Project này focus vào transactional data, không phải event stream analytics |

---

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
