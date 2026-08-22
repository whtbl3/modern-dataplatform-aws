# Modern Data Platform on AWS

## What is this?

A production-ready, serverless data platform built entirely on AWS cloud-native services. The platform enables teams across the organization to automatically ingest, transform, and share data in a governed manner.

## What problem does it solve?

Các tổ chức thường gặp khó khăn khi:
* **Dữ liệu bị phân tán:** Dữ liệu nằm rải rác ở nhiều hệ thống, thiếu một nơi tập trung để truy cập.
* **Thiếu quy trình tự động:** Không có pipeline tự động — các kỹ sư dữ liệu (Data Engineers) phải chạy thủ công từng bước.
* **Thiếu kiểm soát chất lượng:** Dữ liệu không được kiểm soát chất lượng chặt chẽ — lỗi chỉ được phát hiện khi báo cáo ra kết quả sai.
* **Cấp quyền chậm trễ:** Các nhóm mới muốn sử dụng dữ liệu phải chờ đợi nhiều tuần để được cấp quyền.
* **Phát sinh chi phí:** Chi phí tăng vượt tầm kiểm soát khi khối lượng dữ liệu ngày càng lớn.

Nền tảng này giải quyết bằng cách cung cấp:
* **Đường ống dữ liệu tự động (Automated pipelines):** Dữ liệu từ dạng thô (raw) đến đã xử lý (curated) chỉ cần tải tệp lên, quy trình sẽ tự động vận hành.
* **Tự phục vụ kết nối (Self-service onboarding):** Nhóm mới có thể tự tạo miền dữ liệu (domain) riêng chỉ với một câu lệnh.
* **Cổng kiểm soát chất lượng (Data quality gates):** Tự động kiểm tra chất lượng dữ liệu trước khi đưa vào vùng dữ liệu chuẩn (curated zone).
* **Kiểm soát chi phí (Cost control):** Mô hình Serverless (chỉ trả phí khi sử dụng), giới hạn truy vấn Athena, cùng các chính sách quản lý vòng đời dữ liệu (lifecycle policies).
* **Xử lý thời gian thực & theo mẻ (Real-time + Batch):** Hỗ trợ cả truyền dữ liệu liên tục (Kinesis) lẫn tải lên theo mẻ (S3 upload).

## How does it work?

```
[Data Sources] --> [S3 Raw Zone] --> [EventBridge] --> [Lambda Trigger]
                                                            |
                                                            v
                                                  [Step Functions Pipeline]
                                                            |
                                                            v
                                      [Glue Stage A: validate + convert to Iceberg]
                                                            |
                                                            v
                                      [Glue Stage B: business logic + aggregation]
                                                            |
                                                            v
                                                    [S3 Curated Zone]
                                                            |
                                                            v
                                [Athena / QuickSight / Cross-account sharing]
```

## Architecture (10 CDK Stacks)

| Stack | Chuc nang |
|-------|-----------|
| Storage | S3 buckets (raw/staging/curated/analytics/scripts) + IAM |
| Governance | Glue Data Catalog + Lake Formation access control |
| Transform | Glue ETL jobs (Stage A + B) + Crawler |
| Orchestration | Step Functions workflow + EventBridge schedule |
| Monitoring | CloudWatch dashboard + alarms + SNS alerts |
| Ingestion | Lambda trigger khi file moi upload vao S3 |
| DataQuality | Glue Data Quality rules + alert khi fail |
| Streaming | Kinesis stream + Lambda processor |
| Analytics | Athena workgroup + QuickSight role |
| CICD | CodeCommit + CodeBuild + CodePipeline |

## Quick Start

```bash
# 1. Install dependencies
uv sync

# 2. Run tests
uv run pytest tests/unit/ -v

# 3. Generate sample data
uv run python domains/sample-domain/data/generate_sample.py

# 4. Validate CDK stacks
cdk synth --context env=dev --app "uv run python infrastructure/cdk/app.py"

# 5. Deploy (requires AWS credentials)
cdk deploy --all --context env=dev --app "uv run python infrastructure/cdk/app.py"

# 6. Onboard a new domain
uv run python domains/domain-template/onboard.py --domain sales --owner sales@company.com --dataset transactions
```

## Project Structure

```
aws-prj4/
├── infrastructure/cdk/     # CDK stacks (Infrastructure as Code)
├── domains/                # Data domains (sample + template)
├── pipelines/              # CI/CD pipeline definitions
├── tests/                  # Unit + integration tests
└── monitoring/             # Dashboard + alarm definitions
```

## Git Workflow (GitHub Flow)

```
feature/xxx ──●──●──●── Pull Request ──> merge vào main
                                               │
main ──────────────────────────────────────────●──> CDK Pipeline tự deploy
                                                    Dev → Staging → [Approval] → Prod
```

**Quy trình cho MỌI thay đổi (feature, fix, infra, docs):**

1. Tạo branch từ `main` (`git checkout -b fix/ten-loi`)
2. Commit thay đổi trên branch đó
3. Push lên remote, tạo Pull Request → CI tự chạy tests
4. Reviewer approve → Merge vào `main`
5. CDK Pipeline tự động deploy qua 3 environments
6. Xóa branch (đã xong)

**Lưu ý:** Branch là đơn vị công việc ("đang làm gì"), Environment là giai đoạn deploy ("deploy ở đâu"). Hai thứ tách biệt — merge vào `main` 1 lần, pipeline tự promote qua Dev → Staging → Prod.

Chi tiết: [docs/git-branching-strategy.md](docs/git-branching-strategy.md)

## Prerequisites

- Python 3.12+
- Node.js (for CDK CLI)
- AWS CLI configured with appropriate credentials
- `uv` package manager
