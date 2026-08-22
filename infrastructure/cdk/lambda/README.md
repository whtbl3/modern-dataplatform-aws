# Lambda Functions

## Đây là gì?

Source code của các AWS Lambda functions được deploy cùng với CDK stacks. Mỗi file/folder là một Lambda function riêng biệt, xử lý một nhiệm vụ cụ thể trong data pipeline.

## Giải quyết vấn đề gì?

- **Event-driven automation**: Thay vì người phải manually trigger pipeline, Lambda tự động chạy khi có sự kiện (file mới upload, stream data đến, DQ fail)
- **Lightweight processing**: Những tác vụ nhẹ (trigger, alert, format conversion) không cần Glue job nặng nề, Lambda xử lý trong vài giây với chi phí cực thấp
- **Glue code**: Kết nối các AWS services với nhau mà không cần server chạy 24/7

## Hoạt động như thế nào?

Lambda functions được CDK đóng gói (zip) và deploy lên AWS. Mỗi function được gán event source tương ứng:

```
S3 Object Created --> EventBridge --> trigger_pipeline.py --> Start Step Functions
Kinesis Stream --> Lambda Event Source --> streaming/stream_processor.py --> Write to S3
Glue DQ Failed --> EventBridge --> dq_alert.py --> Publish to SNS
```

## Files

| File | Trigger | Chức năng |
|------|---------|-----------|
| `trigger_pipeline.py` | EventBridge (S3 object created) | Kiểm tra file .csv mới, start Step Functions execution |
| `dq_alert.py` | EventBridge (Glue DQ failed) | Parse failed rules, gửi alert qua SNS |
| `streaming/stream_processor.py` | Kinesis Data Stream | Decode records, ghi batch JSON vào S3 raw zone theo partition |
