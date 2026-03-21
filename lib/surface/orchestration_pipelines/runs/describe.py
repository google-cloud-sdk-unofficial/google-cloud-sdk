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
"""Command to describe an orchestration pipeline run details."""

from googlecloudsdk.api_lib.composer import dags_util
from googlecloudsdk.api_lib.composer import util
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.orchestration_pipelines.tools import composer_utils
from googlecloudsdk.core import log
from googlecloudsdk.core import resources


@calliope_base.Hidden
@calliope_base.DefaultUniverseOnly
@calliope_base.ReleaseTracks(calliope_base.ReleaseTrack.BETA)
class Describe(calliope_base.Command):
  """Describe an orchestration pipeline run details."""

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
        help="The full resource name to describe a pipeline run from.",
    )
    parser.add_argument(
        "--bundle",
        required=True,
        help="The ID of the bundle the pipeline belongs to.",
    )
    parser.add_argument(
        "--pipeline",
        required=True,
        help="The ID of the pipeline to describe.",
    )
    parser.add_argument(
        "--run-id",
        required=True,
        help="The ID of the pipeline run.",
    )

  def Run(self, args):
    api_version = util.GetApiVersion(self.ReleaseTrack())

    # 1. List dag runs with filter on bundle, pipeline, and run_id.
    dag_id_filter = composer_utils.build_dag_runs_filter_dag_id(
        bundle=args.bundle, pipeline=args.pipeline
    )
    list_filter = f'{dag_id_filter} AND dag_run_id="{args.run_id}"'
    resource_name = composer_utils.build_resource_name(
        args.environment, args.runner
    )

    dag_ref = resources.REGISTRY.ParseRelativeName(
        resource_name + "/dags/-",
        collection="composer.projects.locations.environments.dags",
        api_version=api_version,
    )
    list_dag_runs_response = dags_util.ListDagRuns(
        dag_ref,
        list_filter=list_filter,
    )
    pipeline_runs = composer_utils.convert_dag_runs_to_pipeline_runs(
        list_dag_runs_response.dagRuns
    )
    if len(pipeline_runs) != 1:
      log.status.Print(
          "No suitable orchestration pipeline run found for bundle"
          f" {args.bundle} and pipeline {args.pipeline} and run id"
          f" {args.run_id}."
      )
      return {"pipelineRuns": []}

    # 2. List task instances for the dag run and convert to actions by
    # aggregating task instances with the same action names.
    dag_run_ref = resources.REGISTRY.ParseRelativeName(
        list_dag_runs_response.dagRuns[0].name,
        collection="composer.projects.locations.environments.dags.dagRuns",
        api_version=api_version,
    )
    list_task_instances_response = dags_util.ListTaskInstances(
        dag_run_ref,
    )
    pipeline_runs[0]["actions"] = (
        composer_utils.aggregate_task_instances_to_actions(
            list_task_instances_response.taskInstances
        )
    )
    return {"pipelineRuns": pipeline_runs}
