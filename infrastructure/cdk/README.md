# CDK Stacks

## What is this?

Day la noi dinh nghia toan bo AWS resources cua data platform bang AWS CDK (Cloud Development Kit). Moi file trong `stacks/` tuong ung voi mot CloudFormation stack - mot nhom resources lien quan duoc deploy va quan ly cung nhau.

## What problem does it solve?

- Thay vi click tay 50+ resources tren AWS Console, chi can chay `cdk deploy`
- Moi resource duoc config voi security best practices (encryption, block public access, least privilege)
- Tach thanh nhieu stacks de co the deploy/update tung phan doc lap
- Parameters hoa theo environment (dev dung it workers, prod dung nhieu hon)

## How does it work?

`app.py` la entry point. No khoi tao tung stack theo thu tu dependency:

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
                                Monitoring (CloudWatch) [doc lap]
```

## Files

| File | Chuc nang |
|------|-----------|
| `app.py` | Entry point - tao tat ca stacks, truyen dependencies giua chung |
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
| `lambda/` | Source code cua cac Lambda functions |
