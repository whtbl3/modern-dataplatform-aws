# Monitoring

## Đây là gì?

Thư mục chứa các định nghĩa cho dashboards và alarms của data platform. Hiện tại monitoring được deploy qua CDK (monitoring_stack.py), folder này dành cho các config bổ sung.

## Giải quyết vấn đề gì?

- **Phát hiện sự cố nhanh**: Alarm báo ngay khi Glue job fail hoặc pipeline timeout
- **Visibility**: Dashboard cho thấy trạng thái pipeline real-time mà không cần check từng service
- **Root cause analysis**: Khi có lỗi, biết ngay cần xem log ở đâu
- **Trend detection**: Nhận ra pipeline chạy chậm dần trước khi nó timeout

## Hoạt động như thế nào?

Monitoring stack tạo:
1. **SNS Topic**: Nơi nhận tất cả alerts, có thể subscribe email/Slack/PagerDuty
2. **CloudWatch Alarms**: Trigger khi Glue job fail hoặc Step Functions execution fail
3. **CloudWatch Dashboard**: Hiển thị Glue job duration và Step Functions success/fail count

```
Glue Job Fail --> CloudWatch Metric --> Alarm --> SNS --> Email/Slack
Step Functions Fail --> CloudWatch Metric --> Alarm --> SNS --> Email/Slack
Glue DQ Fail --> EventBridge --> Lambda --> SNS --> Email/Slack
```

## Cấu trúc

```
monitoring/
├── dashboards/     # Định nghĩa dashboard JSON bổ sung
└── alarms/         # Cấu hình alarm bổ sung
```
