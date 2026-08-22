# Lambda Functions

## What is this?

Source code cua cac AWS Lambda functions duoc deploy cung voi CDK stacks. Moi file/folder la mot Lambda function rieng biet, xu ly mot nhiem vu cu the trong data pipeline.

## What problem does it solve?

- **Event-driven automation**: Thay vi nguoi phai manually trigger pipeline, Lambda tu dong chay khi co su kien (file moi upload, stream data den, DQ fail)
- **Lightweight processing**: Nhung tac vu nhe (trigger, alert, format conversion) khong can Glue job nang ne, Lambda xu ly trong vai giay voi chi phi cuc thap
- **Glue code**: Ket noi cac AWS services voi nhau ma khong can server chay 24/7

## How does it work?

Lambda functions duoc CDK dong goi (zip) va deploy len AWS. Moi function duoc gan event source tuong ung:

```
S3 Object Created --> EventBridge --> trigger_pipeline.py --> Start Step Functions
Kinesis Stream --> Lambda Event Source --> streaming/stream_processor.py --> Write to S3
Glue DQ Failed --> EventBridge --> dq_alert.py --> Publish to SNS
```

## Files

| File | Trigger | Chuc nang |
|------|---------|-----------|
| `trigger_pipeline.py` | EventBridge (S3 object created) | Kiem tra file .csv moi, start Step Functions execution |
| `dq_alert.py` | EventBridge (Glue DQ failed) | Parse failed rules, gui alert qua SNS |
| `streaming/stream_processor.py` | Kinesis Data Stream | Decode records, ghi batch JSON vao S3 raw zone theo partition |
