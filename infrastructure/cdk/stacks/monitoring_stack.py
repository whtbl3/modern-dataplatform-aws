"""
Monitoring Stack - Observability cho data platform.

Tạo 3 thành phần chính:
1. SNS Topic: Kênh trung tâm nhận tất cả alerts (subscribe email, Slack, PagerDuty)
2. CloudWatch Alarms: Phát hiện khi Glue job hoặc Step Functions fail
3. CloudWatch Dashboard: Hiển thị real-time metrics (job duration, success/fail count)

Khi có sự cố, luồng alert là:
  Metric vượt ngưỡng → Alarm ALARM → SNS publish → Email/Slack thông báo
"""
from aws_cdk import (
    Stack,
    Duration,
    aws_cloudwatch as cloudwatch,
    aws_sns as sns,
    aws_sns_subscriptions as subs,
    aws_cloudwatch_actions as cw_actions,
)
from constructs import Construct


class MonitoringStack(Stack):
    """Tạo SNS alerts, CloudWatch alarms, và dashboard cho platform."""

    def __init__(self, scope: Construct, construct_id: str, env_name: str, **kwargs):
        """Khởi tạo monitoring: alert topic, Glue alarm, Step Functions alarm, dashboard."""
        super().__init__(scope, construct_id, **kwargs)

        self.alert_topic = sns.Topic(
            self, "AlertTopic",
            topic_name=f"data-platform-alerts-{env_name}",
            display_name=f"Data Platform Alerts ({env_name})",
        )

        glue_failure_metric = cloudwatch.Metric(
            namespace="Glue",
            metric_name="glue.driver.aggregate.numFailedTasks",
            dimensions_map={"JobName": f"data-platform-stage-a-{env_name}"},
            period=Duration.minutes(5),
            statistic="Sum",
        )

        glue_failure_alarm = cloudwatch.Alarm(
            self, "GlueStageAFailureAlarm",
            alarm_name=f"data-platform-glue-stage-a-failure-{env_name}",
            metric=glue_failure_metric,
            threshold=1,
            evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            alarm_description="Alert when Glue Stage A job has failed tasks",
        )
        glue_failure_alarm.add_alarm_action(cw_actions.SnsAction(self.alert_topic))

        sfn_failure_metric = cloudwatch.Metric(
            namespace="AWS/States",
            metric_name="ExecutionsFailed",
            dimensions_map={"StateMachineArn": f"arn:aws:states:{self.region}:{self.account}:stateMachine:data-platform-pipeline-{env_name}"},
            period=Duration.minutes(5),
            statistic="Sum",
        )

        sfn_failure_alarm = cloudwatch.Alarm(
            self, "StepFunctionsFailureAlarm",
            alarm_name=f"data-platform-pipeline-failure-{env_name}",
            metric=sfn_failure_metric,
            threshold=1,
            evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            alarm_description="Alert when data pipeline Step Functions execution fails",
        )
        sfn_failure_alarm.add_alarm_action(cw_actions.SnsAction(self.alert_topic))

        self.dashboard = cloudwatch.Dashboard(
            self, "PlatformDashboard",
            dashboard_name=f"data-platform-{env_name}",
        )

        self.dashboard.add_widgets(
            cloudwatch.TextWidget(
                markdown=f"# Data Platform Dashboard ({env_name})",
                width=24,
                height=1,
            ),
            cloudwatch.GraphWidget(
                title="Glue Job Duration",
                left=[
                    cloudwatch.Metric(
                        namespace="Glue",
                        metric_name="glue.driver.aggregate.elapsedTime",
                        dimensions_map={"JobName": f"data-platform-stage-a-{env_name}"},
                        statistic="Average",
                        label="Stage A",
                    ),
                    cloudwatch.Metric(
                        namespace="Glue",
                        metric_name="glue.driver.aggregate.elapsedTime",
                        dimensions_map={"JobName": f"data-platform-stage-b-{env_name}"},
                        statistic="Average",
                        label="Stage B",
                    ),
                ],
                width=12,
            ),
            cloudwatch.GraphWidget(
                title="Step Functions Executions",
                left=[
                    sfn_failure_metric,
                    cloudwatch.Metric(
                        namespace="AWS/States",
                        metric_name="ExecutionsSucceeded",
                        dimensions_map={"StateMachineArn": f"arn:aws:states:{self.region}:{self.account}:stateMachine:data-platform-pipeline-{env_name}"},
                        period=Duration.minutes(5),
                        statistic="Sum",
                    ),
                ],
                width=12,
            ),
        )
