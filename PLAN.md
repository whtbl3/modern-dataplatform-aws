# Modern Data Platform on AWS - Kế hoạch triển khai

## 1. Tổng quan dự án

Xây dựng nền tảng dữ liệu hiện đại trên AWS sử dụng các dịch vụ cloud-native serverless, theo DataOps best practices. Platform hỗ trợ multiple data domains, self-service, và scalable từ MVP đến enterprise-grade.

## 2. Mục tiêu kiến trúc

| Mục tiêu | Cách tiếp cận |
|------|----------|
| Linh hoạt & Nhanh nhẹn | Kiến trúc module, IaC, CI/CD pipelines |
| Khả năng mở rộng | Serverless services (Glue, Lambda, Kinesis, Athena) |
| Quản trị tốt | Lake Formation, DataZone, federated governance |
| Bảo mật | Encryption at rest/transit, IAM fine-grained access, audit logging |
| Tự phục vụ | DataZone catalog, automated onboarding templates |

## 3. Thành phần kiến trúc

### 3.1 Tầng lưu trữ dữ liệu
- **Amazon S3** - Lưu trữ chính (raw/staging/curated zones)
- **Apache Iceberg** - Open table format cho transactional data lake
- **Cấu trúc S3 bucket:**
  ```
  s3://platform-raw-zone/          # Vùng tiếp nhận dữ liệu thô
  s3://platform-staging-zone/      # Xử lý trung gian
  s3://platform-curated-zone/      # Dữ liệu sạch, sẵn sàng sử dụng
  s3://platform-analytics-zone/    # Dữ liệu tổng hợp cho BI
  ```

### 3.2 Tầng nạp dữ liệu
- **Amazon Kinesis Data Streams** (on-demand mode) - Streaming thời gian thực
- **AWS DMS** - Migration/CDC từ RDS/on-prem
- **S3 event triggers** - Nạp theo mẻ dựa trên file
- **Amazon MSK** (tuỳ chọn) - Kafka cho high-throughput streaming

### 3.3 Tầng biến đổi dữ liệu
- **AWS Glue** (PySpark) - ETL nặng: transforms, joins, business logic
- **AWS Lambda** (Python/pandas) - Transform nhẹ, event-driven
- **Amazon Athena** (SQL) - SQL-based ELT transforms
- **Các giai đoạn pipeline:**
  - Stage A: Light transform (chuyển đổi format, kiểm tra schema)
  - Stage B: Heavy transform (joins, business logic, tổng hợp)

### 3.4 Tầng điều phối
- **AWS Step Functions** - Điều phối pipeline theo domain
- **Amazon EventBridge** - Trigger và scheduling dựa trên event
- **AWS Glue Workflows** (thay thế) - Điều phối native trong Glue

### 3.5 Quản trị dữ liệu & Catalog
- **AWS Lake Formation** - Kiểm soát truy cập chi tiết, chia sẻ dữ liệu
- **Amazon DataZone** - Business data catalog, khám phá dữ liệu
- **AWS Glue Data Catalog** - Technical metadata catalog
- **Amazon Macie** - Phát hiện PII và phân loại dữ liệu

### 3.6 Tầng tiêu thụ dữ liệu
- **Amazon Athena** - Truy vấn SQL ad-hoc
- **Amazon Redshift Serverless** - Data warehousing workloads
- **Amazon QuickSight** - BI dashboards và visualizations
- **Chia sẻ dữ liệu** - Cross-account qua Lake Formation

### 3.7 Quan sát & Giám sát
- **Amazon CloudWatch** - Metrics, alarms, dashboards
- **CloudWatch Logs** - Logging tập trung
- **Amazon OpenSearch** - Phân tích và tìm kiếm log
- **SNS/Email alerts** - Thông báo lỗi

## 4. DataOps - CI/CD Pipeline

### 4.1 Infrastructure as Code
```
infrastructure/
├── cdk/                    # AWS CDK (Python)
│   ├── app.py
│   ├── stacks/
│   │   ├── storage_stack.py        # S3, Iceberg tables
│   │   ├── ingestion_stack.py      # Kinesis, DMS, triggers
│   │   ├── transform_stack.py      # Glue jobs, Lambda
│   │   ├── orchestration_stack.py  # Step Functions
│   │   ├── governance_stack.py     # Lake Formation, DataZone
│   │   └── monitoring_stack.py     # CloudWatch, alarms
│   └── requirements.txt
├── templates/              # CloudFormation templates (thay thế)
└── configs/
    ├── dev.yaml
    ├── staging.yaml
    └── prod.yaml
```

### 4.2 Quản lý code & Deploy
```
pipelines/
├── platform-pipeline/      # CodePipeline cho infrastructure
│   ├── buildspec.yml       # CodeBuild spec
│   └── pipeline.yaml       # Định nghĩa pipeline
├── transform-pipeline/     # CodePipeline cho ETL code
│   ├── buildspec.yml
│   ├── test/               # Unit tests
│   └── deploy/
└── domain-template/        # Template cho onboarding domain mới
    ├── buildspec.yml
    └── pipeline.yaml
```

### 4.3 Luồng CI/CD
```
Developer commit code
    → CodeCommit (Git repository)
    → CodePipeline triggered
    → CodeBuild: lint + unit tests + security scan
    → Deploy vào DEV (CloudFormation/CDK)
    → Integration tests
    → Manual approval
    → Deploy vào PROD
```

## 5. Cấu trúc Domain/Team

```
domains/
├── domain-template/        # Template cho domains mới
│   ├── transforms/
│   │   ├── stage_a/        # Light transforms
│   │   └── stage_b/        # Heavy transforms
│   ├── tests/
│   ├── config/
│   │   └── datasets.yaml   # Định nghĩa dataset
│   └── pipeline.yaml       # Pipeline riêng cho domain
├── sales/                  # Domain ví dụ
├── marketing/
└── finance/
```

## 6. Các giai đoạn triển khai

### Phase 1 - Nền tảng (MVP) ✓
- [x] Cấu trúc S3 bucket (raw/staging/curated zones)
- [x] IAM roles và policies
- [x] CDK project setup với storage stack
- [x] CodeCommit repository + CodePipeline
- [x] CloudWatch monitoring cơ bản
- [x] Lake Formation setup cơ bản

### Phase 2 - Domain Pipeline đầu tiên ✓
- [x] Nạp sample dataset (batch qua S3)
- [x] Glue job - Stage A (chuyển đổi format sang Iceberg)
- [x] Glue job - Stage B (business logic transform)
- [x] Step Functions điều phối
- [x] Athena queries trên curated data
- [x] Unit tests + CI/CD cho transform code

### Phase 3 - Quản trị & Catalog ✓
- [x] Lake Formation fine-grained access control
- [x] Glue Data Catalog databases
- [x] Macie PII scanning (role + bucket access)
- [x] Data quality checks (Glue Data Quality DQDL rules + alert Lambda)
- [x] EventBridge rule cho DQ failure notifications

### Phase 4 - Streaming & Nâng cao ✓
- [x] Kinesis Data Streams ingestion (on-demand mode)
- [x] Lambda real-time stream processor
- [x] EventBridge scheduling (S3 trigger + daily pipeline)
- [x] Athena workgroup + QuickSight IAM role
- [x] Self-service domain onboarding script

### Phase 5 - Tối ưu & Mở rộng ✓
- [x] Athena query cost control (giới hạn 10 GB scan mỗi query)
- [x] Iceberg table format với partitioning (theo năm)
- [x] CloudWatch dashboard (Glue duration + Step Functions metrics)
- [x] Self-service onboarding automation (onboard.py + domain-template)
- [x] Analytics stack (Athena workgroup, results lifecycle, QuickSight)

## 7. Quyết định công nghệ

| Quyết định | Lựa chọn | Lý do |
|----------|--------|--------|
| Công cụ IaC | AWS CDK (Python) | Best practices tích hợp sẵn, ngôn ngữ quen thuộc |
| Table format | Apache Iceberg | Format mở, AWS hỗ trợ native |
| Transform engine | AWS Glue (PySpark) | Serverless, scalable, tiết kiệm chi phí |
| Điều phối | Step Functions | Serverless, visual workflow, xử lý lỗi tốt |
| Code repo | CodeCommit | Tích hợp native AWS, pricing đơn giản |
| CI/CD | CodePipeline + CodeBuild | Fully managed, tích hợp native |
| Catalog | DataZone + Glue Catalog | Business + technical metadata |
| Query engine | Athena | Serverless, pay-per-query, hỗ trợ Iceberg |

## 8. Cấu trúc dự án (cuối cùng)

```
aws-prj4/
├── PLAN.md                         # File này
├── infrastructure/
│   ├── cdk/                        # CDK stacks
│   └── configs/                    # Cấu hình theo environment
├── pipelines/
│   ├── platform-pipeline/          # CI/CD cho infrastructure
│   └── transform-pipeline/         # CI/CD cho code
├── domains/
│   ├── domain-template/            # Template onboarding
│   └── sample-domain/             # Domain triển khai đầu tiên
├── transforms/
│   ├── common/                     # Utilities transform dùng chung
│   └── sample-domain/
│       ├── stage_a/                # Light transforms
│       └── stage_b/                # Heavy transforms
├── tests/
│   ├── unit/                       # Unit tests
│   └── integration/                # Integration tests
├── monitoring/
│   ├── dashboards/                 # Định nghĩa CloudWatch dashboard
│   └── alarms/                     # Cấu hình alarm
└── docs/
    └── architecture.md             # Tài liệu kiến trúc
```

## 9. Các bước tiếp theo

1. Bắt đầu với Phase 1 - tạo CDK project và storage stack
2. Setup CodeCommit repo + basic CI/CD pipeline
3. Deploy S3 buckets + IAM roles vào AWS account
4. Triển khai domain pipeline đầu tiên (Phase 2)
