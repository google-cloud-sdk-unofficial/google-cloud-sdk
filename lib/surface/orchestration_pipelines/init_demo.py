# -*- coding: utf-8 -*- #
# Copyright 2026 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Init-demo command for orchestration pipelines."""


import pathlib

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.util import files


_PIPELINE_YAML = """\
pipelineId: orchestration-pipeline
description: 'Test deployment pipeline for Dataproc Serverless PySpark job'
runner: 'airflow'
owner: 'data-eng-team'
model_version: 'v1'

defaults:
  project: ${project}
  region: ${region}
  executionConfig:
    retries: 1

triggers:
  - type: schedule
    scheduleInterval: '0 2 * * *'  # 2 AM daily
    startTime: '2025-11-01T00:00:00'
    endTime: '2026-12-01T00:00:00'
    catchup: false
    timezone: 'UTC'

actions:
  - name: test_job
    type: pyspark
    engine:
      engineType: 'dataproc-serverless'
    region: ${region}
    config:
      resourceProfile:
        path: './resources/profiles/serverless-standard.yaml'
    filename: 'jobs/job.py'
"""

_DEPLOYMENT_YAML = """\
environments:
  dev:
    # TODO: Replace with your GCP project
    project: YOUR_PROJECT_ID
    # TODO: Replace with your region
    region: us-central1
    artifact_storage:
      # TODO: Replace with your artifacts bucket
      bucket: YOUR_ARTIFACTS_BUCKET
      path_prefix: pipelines
    # TODO: Replace with your Composer environment
    composer_environment: YOUR_COMPOSER_ENVIRONMENT
    variables:
      # TODO: Replace with your service account
      service_account: YOUR_SERVICE_ACCOUNT
      # TODO: Replace with your network URI
      network_uri: projects/YOUR_PROJECT_ID/global/networks/default
      # TODO: Replace with your subnetwork URI
      subnetwork_uri: projects/YOUR_PROJECT_ID/regions/us-central1/subnetworks/default
    pipelines:
      - source: orchestration-pipeline.yaml
  production:
    # TODO: Replace with your GCP project
    project: YOUR_PROJECT_ID
    # TODO: Replace with your region
    region: us-central1
    artifact_storage:
      # TODO: Replace with your artifacts bucket
      bucket: YOUR_ARTIFACTS_BUCKET
      path_prefix: pipelines
    # TODO: Replace with your Composer environment
    composer_environment: YOUR_COMPOSER_ENVIRONMENT
    variables:
      # TODO: Replace with your service account
      service_account: YOUR_SERVICE_ACCOUNT
      # TODO: Replace with your network URI
      network_uri: projects/YOUR_PROJECT_ID/global/networks/default
      # TODO: Replace with your subnetwork URI
      subnetwork_uri: projects/YOUR_PROJECT_ID/regions/us-central1/subnetworks/default
    pipelines:
      - source: orchestration-pipeline.yaml
"""

_JOB_SCRIPT = """\
\"\"\"
Sensor Temperature Pipeline
Converts raw Celsius readings to Fahrenheit using Pint,
then writes the enriched dataset to GCS.
\"\"\"

import pint
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

# TODO: Replace with your output bucket
GCS_OUTPUT_PATH = "gs://YOUR_OUTPUT_BUCKET/deploy-auto/output"

spark = SparkSession.builder.appName("sensor-temperature-pipeline").getOrCreate()

# Raw sensor readings in Celsius
data = [
    (1, "2025-01-01 00:00", 22.5),
    (1, "2025-01-01 01:00", 23.1),
    (2, "2025-01-01 00:00", 30.0),
    (2, "2025-01-01 01:00", 31.2),
    (3, "2025-01-01 00:00", 17.8),
    (3, "2025-01-01 01:00", 16.4),
]
df = spark.createDataFrame(data, ["sensor_id", "timestamp", "temp_celsius"])

# Convert Celsius -> Fahrenheit using Pint
ureg = pint.UnitRegistry()


@F.udf(returnType="double")
def celsius_to_fahrenheit(c):
    return float((c * ureg.degC).to(ureg.degF).magnitude)


df = df.withColumn("temp_fahrenheit", celsius_to_fahrenheit("temp_celsius"))
df = df.withColumn(
    "status",
    F.when(F.col("temp_celsius") > 30, "HIGH")
    .when(F.col("temp_celsius") < 18, "LOW")
    .otherwise("NORMAL"),
)

df.show(truncate=False)

df.write.mode("overwrite").partitionBy("sensor_id").parquet(GCS_OUTPUT_PATH)
print(f"Wrote {df.count()} records to {GCS_OUTPUT_PATH}")

spark.stop()
"""

_REQUIREMENTS_TXT = 'pint==0.24'

_PROFILE_YAML = """\
profileId: serverless-standard
type: dataproc.session
definition:
  environmentConfig:
    execution_config:
      service_account: "{{{{ service_account }}}}"
      network_uri: "{{{{ network_uri }}}}"
"""

_VALIDATE_WORKFLOW_TEMPLATE = """\
name: Validate Pipelines

on:
  pull_request:
    branches: [main]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: google-github-actions/auth@v2
        with:
          credentials_json: "${{{{ secrets.GCP_SA_KEY }}}}"
      - uses: google-github-actions/setup-gcloud@v1
      - run: gcloud components update --quiet
      - uses: astral-sh/setup-uv@v7
      - run: gcloud orchestration-pipelines validate
"""

_DEPLOY_WORKFLOW_TEMPLATE = """\
name: Deploy to {environment_title}

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: google-github-actions/auth@v2
        with:
          credentials_json: "${{{{ secrets.GCP_SA_KEY }}}}"
      - uses: google-github-actions/setup-gcloud@v1
      - run: gcloud components update --quiet
      - uses: astral-sh/setup-uv@v7
      - run: gcloud orchestration-pipelines deploy --env={environment}
"""


@calliope_base.Hidden
@calliope_base.DefaultUniverseOnly
@calliope_base.ReleaseTracks(calliope_base.ReleaseTrack.BETA)
class InitDemo(calliope_base.Command):
  """Initialize a demo orchestration pipeline project."""

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'directory',
        nargs='?',
        default='orchestration-pipelines-demo',
        help='The directory to initialize the demo in.',
    )

  def Run(self, args):
    work_dir = pathlib.Path.cwd()
    demo_dir = work_dir / args.directory

    if demo_dir.exists():
      raise exceptions.BadFileException(
          f'Directory {demo_dir} already exists. Please specify a new directory'
          ' or remove the existing one.'
      )

    files.MakeDir(str(demo_dir))

    # Create file structure
    self._WriteFile(demo_dir / 'orchestration-pipeline.yaml', _PIPELINE_YAML)
    self._WriteFile(demo_dir / 'deployment.yaml', _DEPLOYMENT_YAML)

    jobs_dir = demo_dir / 'jobs'
    files.MakeDir(str(jobs_dir))
    self._WriteFile(jobs_dir / 'job.py', _JOB_SCRIPT)

    self._WriteFile(jobs_dir / 'requirements.txt', _REQUIREMENTS_TXT)

    profiles_dir = demo_dir / 'resources' / 'profiles'
    files.MakeDir(str(profiles_dir))
    self._WriteFile(profiles_dir / 'serverless-standard.yaml', _PROFILE_YAML)

    self._WriteFile(demo_dir / 'environment.tar.gz', '')

    # Create GitHub workflows
    workflows_dir = demo_dir / '.github' / 'workflows'
    files.MakeDir(str(workflows_dir))

    self._WriteFile(
        workflows_dir / 'validate.yaml', _VALIDATE_WORKFLOW_TEMPLATE
    )

    self._WriteFile(
        workflows_dir / 'deploy-dev.yaml',
        _DEPLOY_WORKFLOW_TEMPLATE.format(
            environment='dev', environment_title='Dev'
        ),
    )

    self._WriteFile(
        workflows_dir / 'deploy-prod.yaml',
        _DEPLOY_WORKFLOW_TEMPLATE.format(
            environment='production', environment_title='Production'
        ),
    )

    log.status.Print(f'Initialized demo project in {demo_dir}')

  def _WriteFile(self, path, content):
    files.WriteFileContents(path, content)
