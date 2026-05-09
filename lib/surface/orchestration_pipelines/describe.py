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
"""Command to describe a pipeline."""

from googlecloudsdk.api_lib.composer import dags_util
from googlecloudsdk.api_lib.composer import util
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.orchestration_pipelines.tools import composer_utils
from googlecloudsdk.command_lib.orchestration_pipelines.tools import yaml_processor
from googlecloudsdk.core import log
from googlecloudsdk.core import resources


@calliope_base.Hidden
@calliope_base.DefaultUniverseOnly
@calliope_base.ReleaseTracks(calliope_base.ReleaseTrack.BETA)
class Describe(calliope_base.Command):
  """Get details about an orchestration pipeline."""

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
        help="The full resource name to describe a pipeline from.",
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
    yaml_processor.add_substitution_flags(parser)

  def Run(self, args):
    api_version = util.GetApiVersion(self.ReleaseTrack())

    # 1. Retrieve the pipeline to be described.
    list_filter = composer_utils.build_dags_filter_tags(
        bundle=args.bundle, pipeline=args.pipeline, is_current=True
    )
    if args.runner:
      env_model = None
    else:
      env_model = yaml_processor.load_environment_with_args(args)

    dags_list = composer_utils.list_pipelines_with_filter(
        list_filter, env_model, args.runner, api_version
    )

    if len(dags_list.dags) != 1:
      log.status.Print(
          f"No specific DAG found for bundle {args.bundle} and pipeline"
          f" {args.pipeline}",
      )
      return {"pipelines": []}
    pipelines = composer_utils.convert_dags_to_pipelines(dags_list.dags)

    # 2. Retrieve the actions for the pipeline.
    dag_ref = resources.REGISTRY.ParseRelativeName(
        dags_list.dags[0].name,
        collection="composer.projects.locations.environments.dags",
        api_version=api_version,
    )
    list_tasks_response = dags_util.ListTasks(dag_ref)
    pipelines[0]["actions"] = composer_utils.convert_tasks_to_actions(
        list_tasks_response.tasks
    )
    return {"pipelines": pipelines}
