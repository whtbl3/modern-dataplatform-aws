# CI/CD Pipelines - DataOps trên AWS

## Đây là gì?

Implementation của DataOps approach theo AWS Well-Architected Data Analytics Lens.
Sử dụng CDK Pipelines (self-mutating pipeline) để tự động hoá toàn bộ lifecycle:
code commit → test → deploy → monitor → alert.

## Giải quyết vấn đề gì?

| Vấn đề | Giải pháp |
|--------|-----------|
| Deploy thủ công hay lỗi | Pipeline tự động, immutable artifacts |
| "Works on my machine" | Cùng 1 artifact deploy vào mọi env |
| Không biết ai sửa gì | Git history + CodePipeline execution logs |
| Deploy lỗi không rollback được | CloudFormation auto-rollback + git revert |
| Không biết deploy có thành công không | SNS alerts on failure + smoke tests |
| Pipeline definition outdated | Self-mutating: pipeline tự update chính nó |

## Hoạt động như thế nào?

### AWS Best Practice: CDK Pipelines (Self-Mutating)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CDK Pipeline                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────┐    ┌──────────────────┐    ┌────────────────────┐         │
│  │  SOURCE  │    │      SYNTH       │    │  UPDATE PIPELINE   │         │
│  │CodeCommit│───>│ Unit Tests       │───>│ (Self-mutation)    │         │
│  │  main    │    │ Lint (ruff)      │    │ Tự cập nhật chính  │         │
│  └──────────┘    │ CDK Synth        │    │ nó nếu code thay   │         │
│                  │ -> cdk.out/      │    │ đổi pipeline def   │         │
│                  └──────────────────┘    └─────────┬──────────┘         │
│                                                     │                    │
│  ┌──────────────────────────────────────────────────┼────────────────┐  │
│  │                    ENVIRONMENTS                   │                │  │
│  ├──────────────────────────────────────────────────┼────────────────┤  │
│  │                                                   ▼                │  │
│  │  ┌─────────────────────────────────────────────────────────┐      │  │
│  │  │ DEV (auto-deploy)                                        │      │  │
│  │  │  Pre:  Unit tests, Lint                                  │      │  │
│  │  │  Deploy: All 9 stacks                                    │      │  │
│  │  │  Post: Integration tests, Deploy transform code          │      │  │
│  │  └────────────────────────────┬────────────────────────────┘      │  │
│  │                                │                                   │  │
│  │                                ▼                                   │  │
│  │  ┌─────────────────────────────────────────────────────────┐      │  │
│  │  │ STAGING (auto-deploy)                                    │      │  │
│  │  │  Pre:  Data contract validation                          │      │  │
│  │  │  Deploy: All 9 stacks                                    │      │  │
│  │  │  Post: Smoke tests, Deploy transform code                │      │  │
│  │  └────────────────────────────┬────────────────────────────┘      │  │
│  │                                │                                   │  │
│  │                                ▼                                   │  │
│  │  ┌─────────────────────────────────────────────────────────┐      │  │
│  │  │ PROD (manual approval required)                          │      │  │
│  │  │  Pre:  Manual Approval (review staging results)          │      │  │
│  │  │  Deploy: All 9 stacks                                    │      │  │
│  │  │  Post: Production verification, Deploy transform code    │      │  │
│  │  └─────────────────────────────────────────────────────────┘      │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ XỬ LÝ LỖI                                                       │    │
│  │  - CloudFormation auto-rollback khi deploy fail                  │    │
│  │  - EventBridge → SNS alert khi pipeline FAILED                   │    │
│  │  - Git revert + re-push để rollback transform code               │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```

### Nguyên tắc DataOps được áp dụng

| Nguyên tắc | Cách triển khai |
|-----------|---------------|
| **Version Control Everything** | CodeCommit: infrastructure, transforms, tests, pipeline definition |
| **Automate Everything** | CDK Pipelines: 0 bước thủ công từ commit đến production |
| **Test Early & Often** | Unit tests (pre-deploy), integration tests (post-dev), smoke tests (post-staging) |
| **Immutable Artifacts** | CDK synth 1 lần, cùng artifact deploy qua 3 envs |
| **Self-Service** | Teams tự push code, pipeline tự deploy, không cần ticket |
| **Observability** | Pipeline failure alerts, test reports, deployment logs |
| **Small Batches** | Mỗi commit = 1 pipeline run, không batch hàng tuần |
| **Rollback Capability** | CloudFormation rollback (infra) + git revert (code) |

### Chiến lược kiểm thử (Shift-Left)

```
                    Chi phí fix bug
                         ▲
                         │         x
                         │       x
                         │     x
                         │   x
                         │ x
                         └──────────────────────>
                         Dev  Staging  Prod  Production Bug

Tầng test:
  1. Unit Tests         (pre-deploy, mỗi commit, 0 AWS cost)
  2. Lint + Security    (pre-deploy, bắt lỗi code style + vulnerabilities)
  3. Data Contracts     (pre-staging, validate DQ rules vẫn đúng)
  4. Integration Tests  (post-dev, chạy với AWS resources thật)
  5. Smoke Tests        (post-staging, verify services running)
  6. Prod Verification  (post-prod, confirm deployment thành công)
```

## Files

| File | Chức năng |
|------|-----------|
| `platform-pipeline/buildspec.yml` | CDK synth step: tests + lint + generate templates |
| `transform-pipeline/buildspec.yml` | Transform code: tests + validate + sync to S3 |

## Thiết lập lần đầu

```bash
# 1. Bootstrap CDK (một lần duy nhất cho mỗi account/region)
cdk bootstrap aws://123456789012/us-east-1

# 2. Deploy pipeline stack (một lần duy nhất, sau đó nó tự update)
cdk deploy DataPlatform-CICD --app "uv run python infrastructure/cdk/app.py"

# 3. Push code lên CodeCommit → pipeline tự động chạy
git remote add codecommit https://git-codecommit.us-east-1.amazonaws.com/v1/repos/data-platform
git push codecommit main
```

## Quy trình Rollback

| Tình huống | Hành động |
|----------|--------|
| Infra deploy fail | CloudFormation tự động rollback, không cần làm gì |
| Transform code bug | `git revert <commit>` + push → pipeline deploy lại code cũ |
| Pipeline definition bug | Pipeline tự update → nếu fail, deploy manual `cdk deploy DataPlatform-CICD` |
| Emergency rollback | `cdk deploy --context env=prod` với commit trước đó |
