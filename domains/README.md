# Domains

## Đây là gì?

Mỗi thư mục con ở đây đại diện cho một data domain - một nhóm dữ liệu thuộc về một team hoặc line of business cụ thể. Đây là nơi data producers viết transform code, định nghĩa data quality rules, và cấu hình pipeline của họ.

## Giải quyết vấn đề gì?

- **Ownership rõ ràng**: Mỗi domain có code riêng, team riêng chịu trách nhiệm
- **Self-service**: Team mới tự onboard bằng cách copy domain-template và chạy onboard.py
- **Isolation**: Domain A không thể vô tình ảnh hưởng đến pipeline của Domain B
- **Standardization**: Tất cả domains đều theo cùng cấu trúc (stage_a, stage_b, data_quality, athena) nên dễ hiểu và maintain

## Hoạt động như thế nào?

Khi một team muốn đưa dữ liệu lên platform:

1. Chạy `onboard.py` để tạo domain mới từ template
2. Cấu hình `config.yaml` (schedule, worker size, governance rules)
3. Viết transform code trong `transforms/stage_a/` và `transforms/stage_b/`
4. Định nghĩa data quality rules
5. Commit + push → CI/CD tự động deploy code lên S3 → Glue job đọc từ đó

## Cấu trúc

```
domains/
├── domain-template/        # Template dùng để tạo domain mới
│   ├── config.yaml         # Template config (điền thông tin domain)
│   └── onboard.py          # Script tự động tạo domain
└── sample-domain/          # Domain mẫu để làm ví dụ
    ├── transforms/         # Code Glue jobs
    ├── data_quality/       # DQDL rules
    ├── athena/             # SQL views cho data consumers
    └── data/               # Sample data + generator
```
