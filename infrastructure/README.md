# Infrastructure

## Đây là gì?

Thư mục chứa toàn bộ Infrastructure as Code (IaC) của data platform. Mọi thành phần AWS (S3, Glue, Lambda, Step Functions, ...) đều được định nghĩa bằng code ở đây, không có gì được tạo thủ công qua AWS Console.

## Giải quyết vấn đề gì?

- **Reproducibility**: Deploy cùng một platform vào dev/staging/prod chỉ bằng 1 lệnh, đảm bảo các môi trường giống nhau
- **Version control**: Mọi thay đổi infrastructure đều được track trong git, có thể rollback bất cứ lúc nào
- **Review process**: Thay đổi phải qua code review trước khi deploy, tránh lỗi do 1 người tự ý sửa
- **Self-documenting**: Đọc code là biết platform gồm những gì, không cần đọc tài liệu riêng

## Hoạt động như thế nào?

Sử dụng AWS CDK (Python) để định nghĩa resources. CDK compile Python code thành CloudFormation templates, rồi CloudFormation deploy lên AWS.

```
Python CDK Code --> CloudFormation Templates --> AWS Resources
(developer viết)    (CDK tự generate)           (CloudFormation deploy)
```

## Cấu trúc

```
infrastructure/
├── cdk/
│   ├── app.py              # Entry point - khởi tạo tất cả stacks
│   ├── cdk.json            # CDK config
│   ├── lambda/             # Lambda function code (deploy cùng CDK)
│   └── stacks/             # Mỗi stack = 1 nhóm resources liên quan
└── configs/
    ├── dev.yaml            # Config riêng cho dev environment
    └── prod.yaml           # Config riêng cho prod environment
```
