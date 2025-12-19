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
"""Command to enable Artifact Registry Platform Logs configuration."""

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.artifacts import flags
from googlecloudsdk.command_lib.artifacts import platformlogs_util
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.GA)
@base.Hidden
@base.UniverseCompatible
class Enable(base.UpdateCommand):
  """Enable the Platform Logs configuration."""

  api_version = 'v1'

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """
          To enable Platform Logs for the project 'my-project' in us-west1 for all severity levels:

            $ {command} --project=my-project --location=us-west1

          To enable Platform Logs for the project 'my-project' in us-west1 for INFO level and above:

            $ {command} --project=my-project --location=us-west1 --severity=INFO

          To enable Platform Logs for the repository 'my-repo' in us-west1 for all severity levels:

            $ {command} --project=my-project --location=us-west1 --repository=my-repo

          To enable Platform Logs for the repository 'my-repo' in us-west1 for INFO level and above:

            $ {command} --project=my-project --location=us-west1 --repository=my-repo --severity=INFO
          """,
  }

  @staticmethod
  def Args(parser):
    """Set up arguments for this command.

    Args:
      parser: An argparse.ArgumentPaser.
    """
    flags.GetPlainRepoFlag().AddToParser(parser)
    flags.GetPlainLocationFlag().AddToParser(parser)
    flags.GetSeverityFlag().AddToParser(parser)

  def Run(self, args):
    """Run the enable command."""
    client = apis.GetClientInstance('artifactregistry', self.api_version)
    messages = client.MESSAGES_MODULE

    platform_logs_config = messages.PlatformLogsConfig(
        loggingState=messages.PlatformLogsConfig.LoggingStateValueValuesEnum.ENABLED
    )

    if args.IsSpecified('severity'):
      platform_logs_config.severityLevel = (
          messages.PlatformLogsConfig.SeverityLevelValueValuesEnum(
              args.severity
          )
      )

    response = platformlogs_util.UpdatePlatformLogsConfig(
        args, client, messages, platform_logs_config
    )
    severity_msg = ' for all severity levels'
    if args.IsSpecified('severity'):
      severity_msg = ' for severity {} and above'.format(args.severity)
    log.status.Print('Enabled Platform Logs for [{}]{}.'.format(
        response.name, severity_msg))
    return response
