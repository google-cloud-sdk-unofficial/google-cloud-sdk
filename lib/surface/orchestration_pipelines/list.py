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
"""Command to list orchestration pipelines."""

from googlecloudsdk.api_lib.composer import util
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.orchestration_pipelines.tools import composer_utils


@calliope_base.Hidden
@calliope_base.DefaultUniverseOnly
@calliope_base.ReleaseTracks(calliope_base.ReleaseTrack.BETA)
class List(calliope_base.Command):
  """List orchestration pipelines in the environment."""

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
        help="The full resource name to list pipelines from.",
    )
    parser.add_argument(
        "--bundle",
        help="The ID of the bundle to filter by.",
    )
    parser.add_argument(
        "--version",
        help="The version of the bundle to filter by.",
    )
    parser.add_argument(
        "--owner",
        help="The owner of the pipeline to filter by.",
    )

  def Run(self, args):
    api_version = util.GetApiVersion(self.ReleaseTrack())

    # 1. Validate arguments and build the filter string.
    if args.version and not args.bundle:
      raise calliope_exceptions.InvalidArgumentException(
          "--version",
          "May not be specified without `--bundle`.",
      )
    list_filter = composer_utils.build_dags_filter_tags(
        bundle=args.bundle,
        version=args.version,
        owner=args.owner,
        is_current=True,
    )
    list_dags_response = composer_utils.list_pipelines_with_filter(
        list_filter,
        args.environment,
        args.runner,
        api_version,
    )

    return {
        "pipelines": composer_utils.convert_dags_to_pipelines(
            list_dags_response.dags
        )
    }
