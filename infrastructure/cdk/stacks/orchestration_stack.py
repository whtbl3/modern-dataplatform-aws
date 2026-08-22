"""
Orchestration Stack - Điều phối trật tự chạy của pipeline.

Tạo Step Functions state machine điều khiển luồng chạy: Stage A → Stage B.
Nếu Stage A fail thì không chạy Stage B (tránh xử lý data lỗi).
Nếu bất kỳ step nào fail, pipeline chuyển sang trạng thái FAILED để alert.

Kèm theo EventBridge rule chạy pipeline tự động mỗi ngày lúc 7:00 UTC.
Pipeline cũng có thể được trigger bởi Lambda (khi có file mới) hoặc manually.
"""
from aws_cdk import (
    Stack,
    Duration,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as tasks,
    aws_events as events,
    aws_events_targets as targets,
)
from constructs import Construct


class OrchestrationStack(Stack):
    """Tạo Step Functions pipeline và EventBridge daily schedule."""

    def __init__(self, scope: Construct, construct_id: str, env_name: str, transform_stack, **kwargs):
        """Khởi tạo state machine: Stage A → Stage B → Success (với error handling)."""
        super().__init__(scope, construct_id, **kwargs)

        stage_a_job_name = transform_stack.stage_a_job.name
        stage_b_job_name = transform_stack.stage_b_job.name

        run_stage_a = tasks.GlueStartJobRun(
            self, "RunStageA",
            glue_job_name=stage_a_job_name,
            integration_pattern=sfn.IntegrationPattern.RUN_JOB,
            result_path="$.stageA",
        )

        run_stage_b = tasks.GlueStartJobRun(
            self, "RunStageB",
            glue_job_name=stage_b_job_name,
            integration_pattern=sfn.IntegrationPattern.RUN_JOB,
            result_path="$.stageB",
        )

        success = sfn.Succeed(self, "PipelineSuccess")

        fail = sfn.Fail(
            self, "PipelineFailed",
            cause="Pipeline execution failed",
        )

        run_stage_a.add_catch(fail, errors=["States.ALL"])
        run_stage_b.add_catch(fail, errors=["States.ALL"])

        definition = run_stage_a.next(run_stage_b).next(success)

        self.state_machine = sfn.StateMachine(
            self, "PipelineStateMachine",
            state_machine_name=f"data-platform-pipeline-{env_name}",
            definition_body=sfn.DefinitionBody.from_chainable(definition),
            timeout=Duration.hours(2),
        )

        events.Rule(
            self, "DailyPipelineTrigger",
            rule_name=f"data-platform-daily-trigger-{env_name}",
            schedule=events.Schedule.cron(hour="7", minute="0"),
            targets=[targets.SfnStateMachine(self.state_machine)],
        )
