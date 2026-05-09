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
"""Command to list orchestration pipeline run history."""

from googlecloudsdk.api_lib.composer import dags_util
from googlecloudsdk.api_lib.composer import util
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.orchestration_pipelines.tools import composer_utils
from googlecloudsdk.command_lib.orchestration_pipelines.tools import yaml_processor
from googlecloudsdk.core import resources


@calliope_base.Hidden
@calliope_base.DefaultUniverseOnly
@calliope_base.ReleaseTracks(calliope_base.ReleaseTrack.BETA)
class List(calliope_base.Command):
  """List orchestration pipelines run history."""

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
        help="The full resource name to list pipeline runs from.",
    )
    parser.add_argument(
        "--bundle",
        required=True,
        help="The ID of the bundle the pipeline runs belong to.",
    )
    parser.add_argument(
        "--pipeline",
        required=True,
        help="The ID of the pipeline to list pipeline runs for.",
    )
    parser.add_argument(
        "--version",
        help="The version of the bundle to list pipeline runs for.",
    )
    yaml_processor.add_substitution_flags(parser)

  def Run(self, args):
    api_version = util.GetApiVersion(self.ReleaseTrack())

    # 1. List dag runs with filter on bundle, pipeline, and/or version.
    list_filter = composer_utils.build_dag_runs_filter_dag_id(
        bundle=args.bundle, pipeline=args.pipeline, version=args.version
    )
    if args.runner:
      resource_name = composer_utils.build_resource_name(runner=args.runner)
    else:
      environment_model = yaml_processor.load_environment_with_args(args)
      resource_name = composer_utils.build_resource_name(
          env_model=environment_model
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

    # 2. Convert dag runs to pipeline runs.
    return {
        "pipeline_runs": composer_utils.convert_dag_runs_to_pipeline_runs(
            list_dag_runs_response.dagRuns
        )
    }
