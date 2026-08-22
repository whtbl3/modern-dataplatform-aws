# CI/CD Pipelines - DataOps on AWS

## What is this?

Implementation cua DataOps approach theo AWS Well-Architected Data Analytics Lens.
Su dung CDK Pipelines (self-mutating pipeline) de tu dong hoa toan bo lifecycle:
code commit -> test -> deploy -> monitor -> alert.

## What problem does it solve?

| Van de | Giai phap |
|--------|-----------|
| Deploy thu cong hay loi | Pipeline tu dong, immutable artifacts |
| "Works on my machine" | Cung 1 artifact deploy vao moi env |
| Khong biet ai sua gi | Git history + CodePipeline execution logs |
| Deploy loi khong rollback duoc | CloudFormation auto-rollback + git revert |
| Khong biet deploy co thanh cong khong | SNS alerts on failure + smoke tests |
| Pipeline definition outdated | Self-mutating: pipeline tu update chinh no |

## How does it work?

### AWS Best Practice: CDK Pipelines (Self-Mutating)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CDK Pipeline                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────┐    ┌──────────────────┐    ┌────────────────────┐         │
│  │  SOURCE  │    │      SYNTH       │    │  UPDATE PIPELINE   │         │
│  │CodeCommit│───>│ Unit Tests       │───>│ (Self-mutation)    │         │
│  │  main    │    │ Lint (ruff)      │    │ Tu cap nhat chinh  │         │
│  └──────────┘    │ CDK Synth        │    │ no neu code thay   │         │
│                  │ -> cdk.out/      │    │ doi pipeline def   │         │
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
│  │ FAILURE HANDLING                                                 │    │
│  │  - CloudFormation auto-rollback khi deploy fail                  │    │
│  │  - EventBridge -> SNS alert khi pipeline FAILED                  │    │
│  │  - Git revert + re-push de rollback transform code               │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```

### DataOps Principles Applied

| Principle | Implementation |
|-----------|---------------|
| **Version Control Everything** | CodeCommit: infrastructure, transforms, tests, pipeline definition |
| **Automate Everything** | CDK Pipelines: 0 manual steps tu commit den production |
| **Test Early & Often** | Unit tests (pre-deploy), integration tests (post-dev), smoke tests (post-staging) |
| **Immutable Artifacts** | CDK synth 1 lan, cung artifact deploy qua 3 envs |
| **Self-Service** | Teams tu push code, pipeline tu deploy, khong can ticket |
| **Observability** | Pipeline failure alerts, test reports, deployment logs |
| **Small Batches** | Moi commit = 1 pipeline run, khong batch hang tuan |
| **Rollback Capability** | CloudFormation rollback (infra) + git revert (code) |

### Testing Strategy (Shift-Left)

```
                    Chi phi fix bug
                         ▲
                         │         x
                         │       x
                         │     x
                         │   x
                         │ x
                         └──────────────────────>
                         Dev  Staging  Prod  Production Bug

Tang test:
  1. Unit Tests         (pre-deploy, moi commit, 0 AWS cost)
  2. Lint + Security    (pre-deploy, bat loi code style + vulnerabilities)
  3. Data Contracts     (pre-staging, validate DQ rules van dung)
  4. Integration Tests  (post-dev, chay voi AWS resources that)
  5. Smoke Tests        (post-staging, verify services running)
  6. Prod Verification  (post-prod, confirm deployment thanh cong)
```

## Files

| File | Chuc nang |
|------|-----------|
| `platform-pipeline/buildspec.yml` | CDK synth step: tests + lint + generate templates |
| `transform-pipeline/buildspec.yml` | Transform code: tests + validate + sync to S3 |

## First-time Setup

```bash
# 1. Bootstrap CDK (mot lan duy nhat cho moi account/region)
cdk bootstrap aws://123456789012/us-east-1

# 2. Deploy pipeline stack (mot lan duy nhat, sau do no tu update)
cdk deploy DataPlatform-CICD --app "uv run python infrastructure/cdk/app.py"

# 3. Push code len CodeCommit -> pipeline tu dong chay
git remote add codecommit https://git-codecommit.us-east-1.amazonaws.com/v1/repos/data-platform
git push codecommit main
```

## Rollback Procedures

| Scenario | Action |
|----------|--------|
| Infra deploy fail | CloudFormation tu dong rollback, khong can lam gi |
| Transform code bug | `git revert <commit>` + push -> pipeline deploy lai code cu |
| Pipeline definition bug | Pipeline tu update -> neu fail, deploy manual `cdk deploy DataPlatform-CICD` |
| Emergency rollback | `cdk deploy --context env=prod` voi commit truoc do |
