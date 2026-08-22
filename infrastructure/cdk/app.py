#!/usr/bin/env python3
"""
CDK Application Entry Point - Modern Data Platform on AWS.

Hai modes van hanh:

1. PIPELINE MODE (mac dinh, dung trong CI/CD):
   Deploy CICDStack - mot self-mutating CDK Pipeline tu dong deploy
   toan bo platform qua 3 environments: Dev -> Staging -> Prod.
   Pipeline tu update chinh no khi code thay doi.

2. STANDALONE MODE (context env=dev/staging/prod):
   Deploy tung stack rieng le cho 1 environment cu the.
   Dung khi can debug hoac deploy thu cong lan dau (bootstrap).

Chay:
  Pipeline mode: cdk deploy DataPlatform-CICD
  Standalone:    cdk synth --context env=dev
"""
import aws_cdk as cdk

from stacks.storage_stack import StorageStack
from stacks.governance_stack import GovernanceStack
from stacks.transform_stack import TransformStack
from stacks.orchestration_stack import OrchestrationStack
from stacks.monitoring_stack import MonitoringStack
from stacks.cicd_stack import CICDStack
from stacks.ingestion_stack import IngestionStack
from stacks.data_quality_stack import DataQualityStack
from stacks.streaming_stack import StreamingStack
from stacks.analytics_stack import AnalyticsStack

app = cdk.App()

env_name = app.node.try_get_context("env") or "dev"

env_config = {
    "dev": cdk.Environment(account="123456789012", region="us-east-1"),
    "staging": cdk.Environment(account="123456789012", region="us-east-1"),
    "prod": cdk.Environment(account="123456789012", region="us-east-1"),
}

# --- Pipeline Mode: Self-mutating CDK Pipeline (deploy once, updates itself) ---
CICDStack(
    app, "DataPlatform-CICD",
    env=env_config["dev"],
)

# --- Standalone Mode: Individual stacks for single environment ---
storage = StorageStack(
    app, f"DataPlatform-Storage-{env_name}",
    env_name=env_name,
    env=env_config.get(env_name),
)

governance = GovernanceStack(
    app, f"DataPlatform-Governance-{env_name}",
    env_name=env_name,
    storage_stack=storage,
    env=env_config.get(env_name),
)

transform = TransformStack(
    app, f"DataPlatform-Transform-{env_name}",
    env_name=env_name,
    storage_stack=storage,
    env=env_config.get(env_name),
)

orchestration = OrchestrationStack(
    app, f"DataPlatform-Orchestration-{env_name}",
    env_name=env_name,
    transform_stack=transform,
    env=env_config.get(env_name),
)

monitoring = MonitoringStack(
    app, f"DataPlatform-Monitoring-{env_name}",
    env_name=env_name,
    env=env_config.get(env_name),
)

ingestion = IngestionStack(
    app, f"DataPlatform-Ingestion-{env_name}",
    env_name=env_name,
    storage_stack=storage,
    state_machine=orchestration.state_machine,
    env=env_config.get(env_name),
)

data_quality = DataQualityStack(
    app, f"DataPlatform-DataQuality-{env_name}",
    env_name=env_name,
    storage_stack=storage,
    alert_topic=monitoring.alert_topic,
    env=env_config.get(env_name),
)

streaming = StreamingStack(
    app, f"DataPlatform-Streaming-{env_name}",
    env_name=env_name,
    storage_stack=storage,
    env=env_config.get(env_name),
)

analytics = AnalyticsStack(
    app, f"DataPlatform-Analytics-{env_name}",
    env_name=env_name,
    storage_stack=storage,
    env=env_config.get(env_name),
)

app.synth()
