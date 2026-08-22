# CDK Stacks

## Đây là gì?

Đây là nơi định nghĩa toàn bộ AWS resources của data platform bằng AWS CDK (Cloud Development Kit). Mỗi file trong `stacks/` tương ứng với một CloudFormation stack - một nhóm resources liên quan được deploy và quản lý cùng nhau.

## Giải quyết vấn đề gì?

- Thay vì click tay 50+ resources trên AWS Console, chỉ cần chạy `cdk deploy`
- Mọi resource được config với security best practices (encryption, block public access, least privilege)
- Tách thành nhiều stacks để có thể deploy/update từng phần độc lập
- Parameters hoá theo environment (dev dùng ít workers, prod dùng nhiều hơn)

## Hoạt động như thế nào?

`app.py` là entry point. Nó khởi tạo từng stack theo thứ tự dependency:

```
Storage (S3 + IAM)
    |
    ├── Governance (Glue Catalog + Lake Formation)
    ├── Transform (Glue Jobs) --> Orchestration (Step Functions)
    │                                   |
    │                                   └── Ingestion (Lambda trigger)
    ├── DataQuality (DQ alert)
    ├── Streaming (Kinesis + Lambda)
    ├── Analytics (Athena + QuickSight)
    └── CICD (CodeCommit + CodePipeline)
                                        |
                                Monitoring (CloudWatch) [độc lập]
```

## Files

| File | Chức năng |
|------|-----------|
| `app.py` | Entry point - tạo tất cả stacks, truyền dependencies giữa chúng |
| `cdk.json` | CDK runtime config (command, default context) |
| `stacks/storage_stack.py` | S3 buckets + Glue IAM role |
| `stacks/governance_stack.py` | Glue databases + Lake Formation |
| `stacks/transform_stack.py` | Glue ETL jobs + Crawler |
| `stacks/orchestration_stack.py` | Step Functions + EventBridge schedule |
| `stacks/monitoring_stack.py` | CloudWatch dashboard + alarms + SNS |
| `stacks/ingestion_stack.py` | EventBridge S3 rule + Lambda trigger |
| `stacks/data_quality_stack.py` | DQ failure alert + Macie PII scanning |
| `stacks/streaming_stack.py` | Kinesis stream + Lambda processor |
| `stacks/analytics_stack.py` | Athena workgroup + QuickSight role |
| `stacks/cicd_stack.py` | CodeCommit repo + CodeBuild + CodePipeline |
| `lambda/` | Source code của các Lambda functions |
