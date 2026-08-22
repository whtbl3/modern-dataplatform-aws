# Monitoring

## What is this?

Thu muc chua cac dinh nghia cho dashboards va alarms cua data platform. Hien tai monitoring duoc deploy qua CDK (monitoring_stack.py), folder nay danh cho cac config bo sung.

## What problem does it solve?

- **Phat hien su co nhanh**: Alarm bao ngay khi Glue job fail hoac pipeline timeout
- **Visibility**: Dashboard cho thay trang thai pipeline real-time ma khong can check tung service
- **Root cause analysis**: Khi co loi, biet ngay can xem log o dau
- **Trend detection**: Nhan ra pipeline chay cham dan truoc khi no timeout

## How does it work?

Monitoring stack tao:
1. **SNS Topic**: Noi nhan tat ca alerts, co the subscribe email/Slack/PagerDuty
2. **CloudWatch Alarms**: Trigger khi Glue job fail hoac Step Functions execution fail
3. **CloudWatch Dashboard**: Hien thi Glue job duration va Step Functions success/fail count

```
Glue Job Fail --> CloudWatch Metric --> Alarm --> SNS --> Email/Slack
Step Functions Fail --> CloudWatch Metric --> Alarm --> SNS --> Email/Slack
Glue DQ Fail --> EventBridge --> Lambda --> SNS --> Email/Slack
```

## Structure

```
monitoring/
├── dashboards/     # Additional dashboard JSON definitions
└── alarms/         # Additional alarm configurations
```
