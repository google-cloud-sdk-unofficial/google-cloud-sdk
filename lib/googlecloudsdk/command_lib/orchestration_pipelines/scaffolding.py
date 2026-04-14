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
"""Scaffolding for orchestration_pipelines init command."""

import pathlib

from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core.util import files


_PIPELINE_TEMPLATE = """\
pipelineId: {pipeline_id}
description: TODO - describe your pipeline
runner: 'airflow'
owner: 'data-eng-team'
modelVersion: 'v2'
defaults:
  projectId: {{{{ project }}}}
  location: {{{{ region }}}}
  executionConfig:
    retries: 1

triggers:
  - schedule:
      interval: '0 2 * * *'  # 2 AM daily
      startTime: '2025-11-01T00:00:00'
      endTime: '2026-12-01T00:00:00'
      catchup: false
      timezone: 'UTC'

# Add your jobs here
actions: []
"""

_DEPLOYMENT_TEMPLATE = """\
environments:
  {environment}:
    # TODO: Replace with your GCP project
    project: "{project_id}"

    # TODO: Replace with your region
    region: "{region}"

    # TODO: Replace with your Composer environment
    composer_environment: "{composer_environment}"

    # TODO: Replace with your artifacts bucket
    artifact_storage:
      bucket: "{artifacts_bucket}"
      path_prefix: pipelines

    variables:
      # TODO: Replace with your service account
      service_account: "{service_account}"
      # TODO: Replace with your network URI
      network_uri: projects/{project_id}/global/networks/default
      # TODO: Replace with your subnetwork URI
      subnetwork_uri: projects/{project_id}/regions/{region}/subnetworks/default

    pipelines:
      - source: {pipeline_file}
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

_VALIDATE_WORKFLOW_TEMPLATE = """\
# This workflow is supposed to run on pull requests to validate the pipelines.
#
# Steps:
# - Checkout code
# - Authenticate to GCP
# - Validate all pipelines listed in deployment.yaml
"""


def InitProject(args):
  """Initializes a orchestration pipeline project."""
  work_dir = pathlib.Path.cwd()
  pipeline_name = args.pipeline_name or 'orchestration-pipeline'
  pipeline_file = f'{pipeline_name}.yaml'
  pipeline_path = work_dir / pipeline_file

  deployment_path = work_dir / 'deployment.yaml'

  workflows_dir = work_dir / '.github' / 'workflows'
  validate_path = workflows_dir / 'validate.yaml'
  deploy_path = workflows_dir / 'deploy.yaml'

  # Check files do not exist first (fail fast)
  files_to_check = [pipeline_path, deployment_path, validate_path, deploy_path]
  existing_files = [f for f in files_to_check if f.exists()]

  if existing_files:
    raise exceptions.BadFileException(
        'The following files already exist: [{}]'.format(
            ', '.join([str(f) for f in existing_files])
        )
    )

  # logical defaults for placeholders
  project_id = args.project or 'YOUR_PROJECT_ID'
  region = args.region or 'YOUR_REGION'
  composer_env = args.composer_environment or 'YOUR_COMPOSER'
  artifacts_bucket = args.artifacts_bucket or 'YOUR_BUCKET'
  service_account = args.service_account or 'YOUR_SERVICE_ACCOUNT'

  # Generate content
  files.WriteFileContents(
      pipeline_path,
      _PIPELINE_TEMPLATE.format(pipeline_id=pipeline_name)
  )

  files.WriteFileContents(
      deployment_path,
      _DEPLOYMENT_TEMPLATE.format(
          environment=args.environment,
          project_id=project_id,
          region=region,
          composer_environment=composer_env,
          artifacts_bucket=artifacts_bucket,
          service_account=service_account,
          pipeline_file=pipeline_file,
      )
  )

  # Ensure dir exists
  files.MakeDir(str(workflows_dir))

  files.WriteFileContents(validate_path, _VALIDATE_WORKFLOW_TEMPLATE)

  files.WriteFileContents(
      deploy_path,
      _DEPLOY_WORKFLOW_TEMPLATE.format(
          environment=args.environment,
          environment_title=args.environment.capitalize()
      )
  )
