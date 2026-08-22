"""
Streaming Stack - Xu ly du lieu real-time tu Kinesis.

Tao Kinesis Data Stream (on-demand mode, tu dong scale theo traffic)
va Lambda processor doc records tu stream, ghi vao S3 raw zone.

On-demand mode: khong can provision shards, AWS tu scale.
Lambda batch: gom 100 records hoac doi 60 giay (whichever comes first) roi xu ly 1 lan.
Output: JSON files phan partition theo year/month/day/hour trong S3 raw zone.

Use case: IoT events, clickstream, real-time transactions tu applications.
"""
from aws_cdk import (
    Stack,
    Duration,
    aws_kinesis as kinesis,
    aws_lambda as _lambda,
    aws_lambda_event_sources as lambda_events,
    aws_iam as iam,
)
from constructs import Construct
from pathlib import Path


class StreamingStack(Stack):
    """Tao Kinesis stream va Lambda processor cho real-time ingestion."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        env_name: str,
        storage_stack,
        **kwargs,
    ):
        super().__init__(scope, construct_id, **kwargs)

        self.stream = kinesis.Stream(
            self, "EventStream",
            stream_name=f"data-platform-events-{env_name}",
            stream_mode=kinesis.StreamMode.ON_DEMAND,
        )

        self.processor_fn = _lambda.Function(
            self, "StreamProcessorFn",
            function_name=f"data-platform-stream-processor-{env_name}",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="stream_processor.handler",
            code=_lambda.Code.from_asset(str(Path(__file__).parent.parent / "lambda" / "streaming")),
            timeout=Duration.minutes(5),
            memory_size=256,
            environment={
                "TARGET_BUCKET": storage_stack.raw_bucket.bucket_name,
                "TARGET_PREFIX": "streaming-events/",
            },
        )

        self.processor_fn.add_event_source(
            lambda_events.KinesisEventSource(
                self.stream,
                starting_position=_lambda.StartingPosition.LATEST,
                batch_size=100,
                max_batching_window=Duration.seconds(60),
                retry_attempts=3,
            )
        )

        storage_stack.raw_bucket.grant_write(self.processor_fn)
        self.stream.grant_read(self.processor_fn)
