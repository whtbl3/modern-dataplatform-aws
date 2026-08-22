"""
Orchestration Stack - Dieu phoi trat tu chay cua pipeline.

Tao Step Functions state machine dieu khien luong chay: Stage A --> Stage B.
Neu Stage A fail thi khong chay Stage B (tranh xu ly data loi).
Neu bat ky step nao fail, pipeline chuyen sang trang thai FAILED de alert.

Kem theo EventBridge rule chay pipeline tu dong moi ngay luc 7:00 UTC.
Pipeline cung co the duoc trigger boi Lambda (khi co file moi) hoac manually.
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
    """Tao Step Functions pipeline va EventBridge daily schedule."""

    def __init__(self, scope: Construct, construct_id: str, env_name: str, transform_stack, **kwargs):
        """Khoi tao state machine: Stage A -> Stage B -> Success (voi error handling)."""
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
