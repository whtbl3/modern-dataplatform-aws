# Tests

## What is this?

Unit tests va integration tests dam bao code hoat dong dung truoc khi deploy. Tests chay local (khong can AWS account) va chay trong CI/CD pipeline.

## What problem does it solve?

- **Phat hien loi som**: Bug duoc bat ngay khi code thay doi, khong doi den production moi biet
- **Refactor an toan**: Khi sua code, tests confirm khong gi bi break
- **Documentation by example**: Doc test la hieu code can xu ly nhung case nao
- **CI gate**: Pipeline chi deploy neu tat ca tests pass

## How does it work?

```bash
uv run pytest tests/unit/ -v
```

Tests su dung `unittest.mock` de mock AWS services (S3, SNS, Step Functions), nen chay duoc ma khong can credentials hay network.

## Structure

```
tests/
├── unit/                           # Chay nhanh, khong can AWS
│   ├── test_transforms.py         # Logic dedup, filter, aggregation
│   ├── test_sample_domain.py      # Data generation + pipeline logic
│   ├── test_lambda_trigger.py     # S3 event trigger Lambda
│   ├── test_streaming.py          # Kinesis stream processor
│   ├── test_data_quality.py       # DQ rules + alert Lambda
│   └── test_onboarding.py         # Domain onboarding script
└── integration/                    # Can AWS account (chua implement)
```
