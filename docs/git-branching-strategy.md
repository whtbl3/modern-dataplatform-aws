# Chiến lược phân nhánh Git - GitHub Flow

## Đây là gì?

Quy định cách team làm việc với Git trong data platform project.
Sử dụng GitHub Flow: nhánh `main` luôn deployable, mọi thay đổi đi qua feature branch + Pull Request.

## Giải quyết vấn đề gì?

- **Tránh deploy code chưa review**: Mọi thay đổi bắt buộc phải qua PR review
- **main luôn stable**: Chỉ code đã được test + approve mới vào main
- **Truy vết được**: Mọi thay đổi có PR link, review comments, approval record
- **Làm song song**: Nhiều người làm nhiều features cùng lúc không conflict

## Hoạt động như thế nào?

```
main ──●────────●────────●────────●────────●──  (luôn deployable)
       │ merge  │ merge  │ merge  │ merge
       │   ▲    │   ▲    │   ▲    │   ▲
       │   │    │   │    │   │    │   │
       │   PR   │   PR   │   PR   │   PR
       │   ▲    │   ▲    │   ▲    │   ▲
       │   │    │   │    │   │    │   │
       └─●─●─●─┘ ●─●──┘  ●─●─●─┘  ●──┘
        feature/  fix/     feature/  fix/
        add-sales dq-rule  streaming alert-format
```

## Nguyên tắc cốt lõi

- **Mỗi thay đổi = 1 branch riêng** (dù là feature, fix, infra, hay docs)
- **Branch chỉ là nơi tạm thời** để làm việc + review, merge xong thì xóa
- **`main` là nơi duy nhất** lưu code chính thức và trigger deployment
- **Không commit trực tiếp vào main** - luôn đi qua Pull Request

## Quy trình làm việc (áp dụng cho TẤT CẢ loại thay đổi)

### Bước 1: Tạo branch từ main

```bash
git checkout main
git pull origin main
git checkout -b fix/dedup-wrong-column      # hoặc feature/, infra/, docs/
```

### Bước 2: Làm việc trên branch, commit thay đổi

```bash
# Sửa code...
git add domains/sample-domain/transforms/stage_a/main.py
git commit -m "fix: sửa logic dedup dùng order_id thay vì toàn bộ columns"

# Thêm test cho phần sửa...
git add tests/unit/test_sample_domain.py
git commit -m "test: thêm test case cho dedup logic mới"
```

### Bước 3: Đẩy branch lên remote

```bash
git push origin fix/dedup-wrong-column
```

### Bước 4: Tạo Pull Request (fix/dedup-wrong-column → main)

- CI tự động chạy unit tests + lint trên branch này
- Gán reviewer phù hợp (xem bảng bên dưới)
- Mô tả rõ: sửa gì, tại sao, test như thế nào

### Bước 5: Review và Merge vào main

```bash
# Sau khi reviewer approve + CI pass:
# Bấm "Merge" trên PR (squash merge recommended)
# → CDK Pipeline tự động trigger: Dev → Staging → [Approval] → Prod
```

### Bước 6: Xóa branch (đã xong việc)

```bash
git branch -d fix/dedup-wrong-column
git push origin --delete fix/dedup-wrong-column
```

## Ví dụ cụ thể cho từng loại branch

### feature/ - Thêm tính năng mới

```bash
git checkout -b feature/sales-add-revenue-transform

# Viết transform code mới
git add domains/sales/transforms/stage_b/main.py
git commit -m "feat: thêm aggregation doanh thu theo ngày cho domain sales"

# Viết tests
git add tests/unit/test_sales_transform.py
git commit -m "test: thêm unit tests cho revenue aggregation"

# Đẩy lên, tạo PR, review, merge
git push origin feature/sales-add-revenue-transform
```

### fix/ - Sửa lỗi

```bash
git checkout -b fix/stage-a-null-handling

# Sửa bug
git add domains/sample-domain/transforms/stage_a/main.py
git commit -m "fix: xử lý null trong cột order_date gây crash Stage A"

git push origin fix/stage-a-null-handling
```

### infra/ - Thay đổi infrastructure

```bash
git checkout -b infra/increase-prod-workers

# Tăng workers cho Glue job production
git add infrastructure/cdk/stacks/transform_stack.py
git commit -m "infra: tăng stage_b workers từ 4 lên 10 cho prod (data tăng 3x)"

git push origin infra/increase-prod-workers
```

### docs/ - Cập nhật tài liệu

```bash
git checkout -b docs/update-onboarding-guide

git add domains/domain-template/README.md
git commit -m "docs: cập nhật hướng dẫn onboard domain mới"

git push origin docs/update-onboarding-guide
```

## Quy tắc đặt tên branch

```
feature/<domain>-<mô-tả-ngắn>    # Tính năng mới
fix/<domain>-<mô-tả-ngắn>        # Sửa lỗi
infra/<mô-tả-ngắn>               # Thay đổi infrastructure
docs/<mô-tả-ngắn>                # Tài liệu
```

## Quy tắc bảo vệ nhánh main

| Quy tắc | Bắt buộc |
|---------|----------|
| Phải tạo PR trước khi merge | Có |
| Phải có ít nhất 1 approval | Có |
| CI (tests + lint) phải pass | Có |
| Branch phải up-to-date với main | Có |
| Cấm force push | Có |
| Cấm xóa nhánh main | Có |

## Ai review ai?

| Loại thay đổi | Reviewer cần thiết |
|---------------|-------------------|
| Transform code (`domains/`) | 1 data engineer + 1 platform engineer |
| Infrastructure (`infrastructure/`) | 2 platform engineers |
| Data quality rules | Domain owner + 1 data engineer |
| Pipeline/CI/CD | 2 platform engineers |
| Tests | 1 engineer (bất kỳ) |
| Docs | 1 engineer (bất kỳ) |

## Quy ước commit message

```
<loại>: <mô tả ngắn gọn>

<phần body (không bắt buộc) - giải thích TẠI SAO, không phải LÀM GÌ>
```

**Các loại:**

| Loại | Khi nào dùng |
|------|-------------|
| `feat` | Thêm tính năng mới (transform mới, domain mới, service mới) |
| `fix` | Sửa lỗi (bug trong transform logic, config sai) |
| `infra` | Thay đổi infrastructure (thêm workers, đổi schedule) |
| `test` | Thêm/sửa tests |
| `docs` | Tài liệu |
| `refactor` | Sửa code nhưng không đổi behavior |

**Ví dụ:**
```
feat: thêm aggregation doanh thu hàng ngày cho domain sales

Yêu cầu từ Finance team: cần báo cáo doanh thu theo category
cho quarterly reporting. Aggregate orders theo date/category/region.

fix: sửa logic dedup trong stage_a chỉ dùng order_id

Trước đó dedup dùng tất cả columns, gây false negatives khi
cùng order có timestamps khác nhau do retry.

infra: tăng stage_b workers từ 4 lên 10 cho prod

Data volume tăng 3x tháng trước, job bị timeout vào giờ cao điểm.
```

## Quy trình Hotfix (khẩn cấp production)

Khi production có lỗi cần fix gấp:

```bash
# 1. Tạo branch từ main (mới nhất)
git checkout main && git pull
git checkout -b fix/prod-urgent-dq-rule

# 2. Sửa lỗi + chạy test local
git add ...
git commit -m "fix: sửa DQ rule chặn data hợp lệ trên production"

# 3. Push + tạo PR với label "HOTFIX"
git push origin fix/prod-urgent-dq-rule
# Tạo PR, đánh tag HOTFIX, yêu cầu review nhanh

# 4. Merge sau 1 approval (không cần 2 như bình thường)
# Pipeline deploy: Dev → Staging → [Bỏ qua approval] → Prod
```

## Tích hợp với CDK Pipeline

```
Nhánh feature/fix/infra/docs (KHÔNG trigger deploy):
  push → CI chạy unit tests + lint (kiểm tra code OK)
  → Chỉ báo pass/fail, KHÔNG deploy gì cả

Nhánh main (sau khi merge PR - trigger FULL deploy):
  merge → CDK Pipeline tự động chạy:
    Synth → Deploy Dev → Integration tests
          → Deploy Staging → Smoke tests
          → [Manual Approval] → Deploy Prod
```

## Branch và Environment là hai thứ KHÁC NHAU

**Điểm quan trọng nhất:** Branch KHÔNG map với environment.

```
❌ SAI (cách GitFlow cũ):
   nhánh develop  → deploy vào Dev
   nhánh release  → deploy vào Staging
   nhánh main     → deploy vào Prod

✅ ĐÚNG (GitHub Flow + CDK Pipelines):
   nhánh main → Pipeline TỰ ĐỘNG promote qua: Dev → Staging → Prod
```

### Branch trả lời: "Đang làm gì?"

| Branch | Ý nghĩa |
|--------|---------|
| `feature/sales-revenue` | Đang thêm tính năng revenue cho domain sales |
| `fix/dedup-logic` | Đang sửa lỗi dedup |
| `infra/more-workers` | Đang tăng workers |

### Environment trả lời: "Code deploy ở đâu?"

| Environment | Vai trò | Khi nào deploy |
|-------------|---------|---------------|
| **Dev** | Kiểm tra code chạy đúng với AWS thật | Tự động sau merge |
| **Staging** | Mô phỏng production, chạy smoke tests | Tự động sau Dev pass |
| **Prod** | Phục vụ người dùng thật | Sau khi người approve |

### Cùng 1 code, khác config

Pipeline lấy **cùng 1 artifact** (output của `cdk synth`) rồi deploy vào 3 environments.
Khác nhau chỉ ở **config** (`dev.yaml` vs `prod.yaml`):

| Cấu hình | Dev | Staging | Prod |
|-----------|-----|---------|------|
| Glue Workers | 2 (nhỏ, rẻ) | 4 (trung bình) | 10 (mạnh) |
| Schedule | 7:00 UTC | 7:00 UTC | 6:00 UTC |
| Alert gửi cho | dev team | dev team | oncall team |
| S3 Bucket | `...-dev-123` | `...-staging-123` | `...-prod-123` |
| Cần approve | Không | Không | **Có** |
| Data volume | Nhỏ (sample) | Trung bình (copy) | Lớn (thật) |

### Tại sao tách Branch và Environment?

1. **Tránh "works on dev but not prod"**: Cùng 1 artifact, không build lại cho từng env
2. **Tốc độ**: Không cần branch riêng cho từng env → merge 1 lần, deploy 3 nơi
3. **Đơn giản**: Chỉ cần quan tâm `main` branch, pipeline lo phần còn lại
4. **An toàn**: Code phải pass Dev + Staging trước khi lên Prod (không bypass được)

### Minh họa toàn bộ flow

```
Developer A                Developer B
    │                          │
    │ feature/add-sales        │ fix/null-handling
    │     │                    │     │
    │     ●──●──●              │     ●──●
    │         │                │       │
    │     tạo PR               │   tạo PR
    │         │                │       │
    ▼         ▼                ▼       ▼
main ────────●────────────────●──────────── (2 merges)
              │                │
              ▼                ▼
         CDK Pipeline     CDK Pipeline
         (lần chạy 1)    (lần chạy 2)
              │                │
              ├─ Dev ✓         ├─ Dev ✓
              ├─ Staging ✓     ├─ Staging ✓
              ├─ Approve ✓     ├─ Approve ✓
              └─ Prod ✓        └─ Prod ✓
```

## Git Hooks (chạy local, không bắt buộc)

Cài đặt để tự kiểm tra trước khi commit/push:

```bash
# pre-commit: chạy tests trước khi commit (bắt lỗi sớm)
uv run pytest tests/unit/ -x --tb=short

# pre-push: chạy lint trước khi push (đảm bảo code sạch)
ruff check domains/ infrastructure/cdk/stacks/
```
