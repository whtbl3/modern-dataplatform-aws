# Modern Data Platform on AWS - Implementation Plan

## 1. Project Overview

Build a modern data platform on AWS using cloud-native serverless services, following DataOps best practices. Platform sẽ hỗ trợ multiple data domains, self-service, và scalable từ MVP đến enterprise-grade.

## 2. Architecture Goals

| Goal | Approach |
|------|----------|
| Flexible & Agile | Modular architecture, IaC, CI/CD pipelines |
| Scalable | Serverless services (Glue, Lambda, Kinesis, Athena) |
| Well-Governed | Lake Formation, DataZone, federated governance |
| Secure | Encryption at rest/transit, IAM fine-grained access, audit logging |
| Self-Serve | DataZone catalog, automated onboarding templates |

## 3. Architecture Components

### 3.1 Data Storage Layer
- **Amazon S3** - Primary storage (raw/staging/curated zones)
- **Apache Iceberg** - Open table format for transactional data lake
- **S3 bucket structure:**
  ```
  s3://platform-raw-zone/          # Landing zone for raw data
  s3://platform-staging-zone/      # Intermediate processing
  s3://platform-curated-zone/      # Clean, business-ready data
  s3://platform-analytics-zone/    # Aggregated data for BI
  ```

### 3.2 Data Ingestion Layer
- **Amazon Kinesis Data Streams** (on-demand mode) - Real-time streaming
- **AWS DMS** - Database migration/CDC from RDS/on-prem
- **S3 event triggers** - File-based batch ingestion
- **Amazon MSK** (optional) - Kafka for high-throughput streaming

### 3.3 Data Transformation Layer
- **AWS Glue** (PySpark) - Heavy ETL transforms, joins, business logic
- **AWS Lambda** (Python/pandas) - Light transforms, event-driven
- **Amazon Athena** (SQL) - SQL-based ELT transforms
- **Pipeline stages:**
  - Stage A: Light transform (file format conversion, schema validation)
  - Stage B: Heavy transform (joins, business logic, aggregations)

### 3.4 Data Orchestration Layer
- **AWS Step Functions** - Pipeline orchestration per domain
- **Amazon EventBridge** - Event-driven triggers and scheduling
- **AWS Glue Workflows** (alternative) - Native Glue orchestration

### 3.5 Data Governance & Catalog
- **AWS Lake Formation** - Fine-grained access control, data sharing
- **Amazon DataZone** - Business data catalog, data discovery
- **AWS Glue Data Catalog** - Technical metadata catalog
- **Amazon Macie** - PII detection and data classification

### 3.6 Data Consumption Layer
- **Amazon Athena** - Ad-hoc SQL queries
- **Amazon Redshift Serverless** - Data warehousing workloads
- **Amazon QuickSight** - BI dashboards and visualizations
- **Data sharing** - Cross-account via Lake Formation

### 3.7 Observability & Monitoring
- **Amazon CloudWatch** - Metrics, alarms, dashboards
- **CloudWatch Logs** - Centralized logging
- **Amazon OpenSearch** - Log analytics and search
- **SNS/Email alerts** - Failure notifications

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
├── templates/              # CloudFormation templates (alternative)
└── configs/
    ├── dev.yaml
    ├── staging.yaml
    └── prod.yaml
```

### 4.2 Code Management & Deployment
```
pipelines/
├── platform-pipeline/      # CodePipeline for infrastructure
│   ├── buildspec.yml       # CodeBuild spec
│   └── pipeline.yaml       # Pipeline definition
├── transform-pipeline/     # CodePipeline for ETL code
│   ├── buildspec.yml
│   ├── test/               # Unit tests
│   └── deploy/
└── domain-template/        # Template for new domain onboarding
    ├── buildspec.yml
    └── pipeline.yaml
```

### 4.3 CI/CD Flow
```
Developer commits code
    → CodeCommit (Git repository)
    → CodePipeline triggered
    → CodeBuild: lint + unit tests + security scan
    → Deploy to DEV (CloudFormation/CDK)
    → Integration tests
    → Manual approval
    → Deploy to PROD
```

## 5. Domain/Team Structure

```
domains/
├── domain-template/        # Cookiecutter template for new domains
│   ├── transforms/
│   │   ├── stage_a/        # Light transforms
│   │   └── stage_b/        # Heavy transforms
│   ├── tests/
│   ├── config/
│   │   └── datasets.yaml   # Dataset definitions
│   └── pipeline.yaml       # Domain-specific pipeline
├── sales/                  # Example domain
├── marketing/
└── finance/
```

## 6. Implementation Phases

### Phase 1 - Foundation (MVP) ✓
- [x] S3 bucket structure (raw/staging/curated zones)
- [x] IAM roles and policies
- [x] CDK project setup with storage stack
- [x] CodeCommit repository + CodePipeline
- [x] CloudWatch basic monitoring
- [x] Lake Formation basic setup

### Phase 2 - First Domain Pipeline ✓
- [x] Sample dataset ingestion (batch via S3)
- [x] Glue job - Stage A (format conversion to Iceberg)
- [x] Glue job - Stage B (business logic transform)
- [x] Step Functions orchestration
- [x] Athena queries on curated data
- [x] Unit tests + CI/CD for transform code

### Phase 3 - Governance & Catalog ✓
- [x] Lake Formation fine-grained access control
- [x] Glue Data Catalog databases
- [x] Macie PII scanning (role + bucket access)
- [x] Data quality checks (Glue Data Quality DQDL rules + alert Lambda)
- [x] EventBridge rule for DQ failure notifications

### Phase 4 - Streaming & Advanced ✓
- [x] Kinesis Data Streams ingestion (on-demand mode)
- [x] Lambda real-time stream processor
- [x] EventBridge scheduling (S3 trigger + daily pipeline)
- [x] Athena workgroup + QuickSight IAM role
- [x] Self-service domain onboarding script

### Phase 5 - Optimization & Scale ✓
- [x] Athena query cost control (10 GB scan limit per query)
- [x] Iceberg table format with partitioning (year-based)
- [x] CloudWatch dashboard (Glue duration + Step Functions metrics)
- [x] Self-service onboarding automation (onboard.py + domain-template)
- [x] Analytics stack (Athena workgroup, results lifecycle, QuickSight)

## 7. Technology Decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| IaC tool | AWS CDK (Python) | Best practices built-in, familiar language |
| Table format | Apache Iceberg | Open format, AWS native support |
| Transform engine | AWS Glue (PySpark) | Serverless, scalable, cost-effective |
| Orchestration | Step Functions | Serverless, visual workflow, error handling |
| Code repo | CodeCommit | AWS-native integration, simple pricing |
| CI/CD | CodePipeline + CodeBuild | Fully managed, native integration |
| Catalog | DataZone + Glue Catalog | Business + technical metadata |
| Query engine | Athena | Serverless, pay-per-query, Iceberg support |

## 8. Project Structure (Final)

```
aws-prj4/
├── PLAN.md                         # This file
├── infrastructure/
│   ├── cdk/                        # CDK stacks
│   └── configs/                    # Environment configs
├── pipelines/
│   ├── platform-pipeline/          # Infra CI/CD
│   └── transform-pipeline/         # Code CI/CD
├── domains/
│   ├── domain-template/            # Onboarding template
│   └── sample-domain/             # First domain implementation
├── transforms/
│   ├── common/                     # Shared transform utilities
│   └── sample-domain/
│       ├── stage_a/                # Light transforms
│       └── stage_b/                # Heavy transforms
├── tests/
│   ├── unit/                       # Unit tests
│   └── integration/                # Integration tests
├── monitoring/
│   ├── dashboards/                 # CloudWatch dashboard definitions
│   └── alarms/                     # Alarm configurations
└── docs/
    └── architecture.md             # Architecture documentation
```

## 9. Next Steps

1. Bắt đầu với Phase 1 - tạo CDK project và storage stack
2. Setup CodeCommit repo + basic CI/CD pipeline
3. Deploy S3 buckets + IAM roles vào AWS account
4. Implement first domain pipeline (Phase 2)
