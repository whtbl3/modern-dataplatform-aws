# Cấu hình theo môi trường

## Đây là gì?

YAML files chứa cấu hình riêng cho mỗi environment (dev, staging, prod). Cùng 1 CDK code nhưng deploy khác nhau tuỳ môi trường.

## Giải quyết vấn đề gì?

- **Dev rẻ hơn**: Dev dùng ít workers (G.1X, 2 workers) → chi phí thấp khi test
- **Prod mạnh hơn**: Prod dùng nhiều workers (G.2X, 10 workers) → xử lý data lớn nhanh
- **Tách biệt alert**: Dev alert gửi cho dev team, Prod alert gửi cho oncall
- **Một code base**: Không cần maintain 3 bản code khác nhau cho 3 environments

## Hoạt động như thế nào?

CDK đọc `env` context variable, chọn config tương ứng, truyền vào các stacks.

```python
cdk deploy --context env=dev   # → đọc dev.yaml
cdk deploy --context env=prod  # → đọc prod.yaml
```

## Files

| File | Environment | Đặc điểm |
|------|-------------|----------|
| `dev.yaml` | Development | Workers nhỏ, alert gửi dev team |
| `prod.yaml` | Production | Workers lớn, alert gửi oncall team |
