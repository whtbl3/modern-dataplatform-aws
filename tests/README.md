# Tests

## Đây là gì?

Unit tests và integration tests đảm bảo code hoạt động đúng trước khi deploy. Tests chạy local (không cần AWS account) và chạy trong CI/CD pipeline.

## Giải quyết vấn đề gì?

- **Phát hiện lỗi sớm**: Bug được bắt ngay khi code thay đổi, không đợi đến production mới biết
- **Refactor an toàn**: Khi sửa code, tests confirm không gì bị break
- **Documentation by example**: Đọc test là hiểu code cần xử lý những case nào
- **CI gate**: Pipeline chỉ deploy nếu tất cả tests pass

## Hoạt động như thế nào?

```bash
uv run pytest tests/unit/ -v
```

Tests sử dụng `unittest.mock` để mock AWS services (S3, SNS, Step Functions), nên chạy được mà không cần credentials hay network.

## Cấu trúc

```
tests/
├── unit/                           # Chạy nhanh, không cần AWS
│   ├── test_transforms.py         # Logic dedup, filter, aggregation
│   ├── test_sample_domain.py      # Data generation + pipeline logic
│   ├── test_lambda_trigger.py     # S3 event trigger Lambda
│   ├── test_streaming.py          # Kinesis stream processor
│   ├── test_data_quality.py       # DQ rules + alert Lambda
│   └── test_onboarding.py         # Domain onboarding script
└── integration/                    # Cần AWS account (chưa implement)
```
