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
"""Command to trigger an orchestration pipeline."""

import datetime
import random
import time
from googlecloudsdk.api_lib.composer import dags_util
from googlecloudsdk.api_lib.composer import util
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.orchestration_pipelines.tools import composer_utils
from googlecloudsdk.core import log
from googlecloudsdk.core import resources

DEFAULT_POLLING_TIME_SECONDS = datetime.timedelta(seconds=2)
POLL_JITTER_SECONDS = datetime.timedelta(seconds=0.5)


@calliope_base.Hidden
@calliope_base.DefaultUniverseOnly
@calliope_base.ReleaseTracks(calliope_base.ReleaseTrack.BETA)
class Trigger(calliope_base.Command):
  """Trigger an orchestration pipeline."""

  @staticmethod
  def Args(parser):
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--environment",
        help=(
            "The target environment of the pipeline, as defined in"
            " deployment.yaml."
        ),
    )
    group.add_argument(
        "--runner",
        help="The full resource name to trigger a pipeline from.",
    )
    parser.add_argument(
        "--bundle",
        required=True,
        help="The ID of the bundle the pipeline belongs to.",
    )
    parser.add_argument(
        "--pipeline",
        required=True,
        help="The ID of the pipeline to trigger.",
    )
    parser.add_argument(
        "--async",
        dest="async_",
        action="store_true",
        help="Whether to trigger the pipeline run asynchronously.",
    )

  def Run(self, args):
    api_version = util.GetApiVersion(self.ReleaseTrack())

    # 1. Retrieve the pipeline to be triggered.
    list_filter = composer_utils.build_dags_filter_tags(
        bundle=args.bundle, pipeline=args.pipeline, is_current=True
    )
    dags_list = composer_utils.list_pipelines_with_filter(
        list_filter, args.environment, args.runner, api_version
    )

    if len(dags_list.dags) == 0:
      return {
          "result": "failed",
          "reason": "No pipeline found for given bundle and pipeline IDs.",
      }

    if len(dags_list.dags) > 1:
      return {
          "result": "failed",
          "reason": (
              "Multiple pipelines found for given bundle and pipeline IDs."
          ),
      }

    # 2. Trigger the pipeline.
    log.status.Print(
        f"Triggering pipeline run for {dags_list.dags[0].dagId}..."
    )
    dag_ref = resources.REGISTRY.ParseRelativeName(
        dags_list.dags[0].name,
        collection="composer.projects.locations.environments.dags",
        api_version=api_version,
    )
    trigger_dag_response = dags_util.TriggerDag(
        dag_ref,
    )

    # 3. If async, return the trigger pipeline run response.
    if args.async_:
      return {
          "result": "success",
          "pipelineRuns": composer_utils.convert_dag_runs_to_pipeline_runs(
              [trigger_dag_response]
          ),
      }

    # 4. Wait for the pipeline run to finish by polling the DAG run state.
    dag_run_ref = resources.REGISTRY.ParseRelativeName(
        trigger_dag_response.name,
        collection="composer.projects.locations.environments.dags.dagRuns",
        api_version=api_version,
    )
    while True:
      try:
        dag_run = dags_util.GetDagRun(dag_run_ref)
        if dag_run.state.name == "FAILED":
          return {
              "result": "failed",
              "reason": f"Pipeline run {dag_run.dagRunId} failed.",
          }
        if dag_run.state.name == "SUCCEEDED":
          return {
              "result": "success",
              "pipelineRuns": composer_utils.convert_dag_runs_to_pipeline_runs(
                  [dag_run]
              ),
          }

        time.sleep(
            DEFAULT_POLLING_TIME_SECONDS.total_seconds()
            + random.uniform(
                -POLL_JITTER_SECONDS.total_seconds(),
                POLL_JITTER_SECONDS.total_seconds(),
            )
        )
      except KeyboardInterrupt:
        break
    return {
        "result": "success",
        "reason": (
            "The command was interrupted, but the process is still running"
            " in the background."
        ),
    }
