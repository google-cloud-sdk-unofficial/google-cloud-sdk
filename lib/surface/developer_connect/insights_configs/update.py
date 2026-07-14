# -*- coding: utf-8 -*- #
# Copyright 2025 Google LLC. All Rights Reserved.
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
"""Update the configuration of an insight config."""

import datetime
import textwrap

from googlecloudsdk.api_lib.developer_connect.insights_configs import insights_config
from googlecloudsdk.api_lib.util import exceptions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.developer_connect import flags
from googlecloudsdk.command_lib.developer_connect import resource_args
from googlecloudsdk.core import log

DETAILED_HELP = {
    'DESCRIPTION': """
          Update the configuration of an insights config.
          """,
    'EXAMPLES': """
          To update the state of an insights config, run:

            $ {command} insights-config-name --run-discovery

          To update the Artifact Analysis project for an artifact in an insights config, run:

            $ {command} insights-config-name --artifact-uri=us-{location}-docker.pkg.dev/my-project/my-artifact-repo/my-image --build-project={build_project}
          """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA)
@base.DefaultUniverseOnly
class Update(base.UpdateCommand):
  """Update the configuration of an insight config."""

  @staticmethod
  def Args(parser):
    """Adds arguments for this command."""
    try:
      resource_args.AddInsightConfigResourceArg(parser, verb='update')
    except exceptions.HttpException:
      log.status.Print('Failed to add insight config resource argument.')
      raise

    # Relevant arguments and groups.
    update_group = parser.add_group(
        required=True, help='Update the insight config.'
    )
    artifact_group = update_group.add_group()
    flags.AddDiscoveryArgument(update_group)
    flags.AddArtifactArgument(artifact_group)
    flags.AddBuildProjectArgument(artifact_group)

  def Run(self, args):
    max_wait = datetime.timedelta(seconds=30)
    client = insights_config.InsightsConfigClient(self.ReleaseTrack())
    insights_config_ref = args.CONCEPTS.insights_config.Parse()
    try:
      operation = client.update(
          insight_config_ref=insights_config_ref,
          discovery=args.run_discovery,
          build_project=args.build_project,
          artifact_uri=args.artifact_uri,
          app_hub=getattr(args, 'app_hub_application', None),
          target_projects=getattr(args, 'target_projects', None),
      )
    except exceptions.HttpException:
      log.status.Print('Failed to update the insight config {}.'.format(
          insights_config_ref.RelativeName()
      ))
      raise

    log.status.Print('Updating the insight config {}.'.format(
        insights_config_ref.RelativeName()
    ))

    return client.wait_for_operation(
        operation_ref=client.get_operation_ref(operation),
        message='Waiting for operation [{}] to be completed...'
        .format(
            client.get_operation_ref(operation).RelativeName()),
        has_result=True,
        max_wait=max_wait,
    )


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
class UpdateAlpha(Update):
  """Update command for insight configurations in Alpha."""

  @classmethod
  def Args(cls, parser):
    """Add arguments for Alpha."""
    try:
      resource_args.AddInsightConfigResourceArg(parser, verb='update')
    except exceptions.HttpException:
      log.status.Print('Failed to add insight config resource argument.')
      raise

    update_group = parser.add_group(
        required=True, help='Update the insight config.'
    )
    artifact_group = update_group.add_group()
    flags.AddDiscoveryArgument(update_group)
    flags.AddArtifactArgument(artifact_group)
    flags.AddBuildProjectArgument(artifact_group)

    context_group = update_group.add_mutually_exclusive_group(hidden=True)
    context_group.add_argument(
        '--app-hub-application',
        metavar='APP_HUB_APPLICATION',
        dest='app_hub_application',
        hidden=True,
        help='The App Hub application of the insight config.',
    )
    context_group.add_argument(
        '--target-projects',
        metavar='TARGET_PROJECTS',
        dest='target_projects',
        type=arg_parsers.ArgList(),
        hidden=True,
        help=textwrap.dedent("""\
          A comma-separated list of target project IDs/numbers of the insight config.

          Format examples:
          `--target-projects=123567890,my-project`
          `--target-projects=projects/1234567890,projects/my-project`
          """),
    )

Update.detailed_help = DETAILED_HELP
UpdateAlpha.detailed_help = DETAILED_HELP
