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

"""api registry mcp server enable command."""

from googlecloudsdk.api_lib.api_registry import resources
from googlecloudsdk.api_lib.services import exceptions
from googlecloudsdk.api_lib.services import services_util
from googlecloudsdk.api_lib.services import serviceusage
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log


# TODO(b/321801975) make command public after preview.
@base.UniverseCompatible
@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Enable(base.SilentCommand):
  """Enables MCP Server for a given service in the current project."""

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'service',
        help='The MCP server to enable.',
    )

  def Run(self, args):
    """Enables MCP Server for a given service in the current project."""
    project_resource = resources.GetProjectResource()

    # check if sevice has Mcp Config
    try:
      service_metadata = serviceusage.GetServiceV2Beta(
          f'{project_resource}/services/{args.service}')
    except exceptions.GetServiceException:
      log.error(
          f'Service {args.service} not found or permission_denied.')
      return

    if not service_metadata.state.enableRules:
      track = self.ReleaseTrack()
      track_prefix = ''
      if track == base.ReleaseTrack.ALPHA:
        track_prefix = 'alpha '
      elif track == base.ReleaseTrack.BETA:
        track_prefix = 'beta '
      # GA commands do not have a 'ga' prefix, so it remains empty

      enable_command = f'gcloud {track_prefix}services enable {args.service}'
      log.warning(
          'To enable the MCP endpoint, the service must'
          ' be enabled first. Please run the following command to enable the'
          f' service: {enable_command}.')

    op = serviceusage.AddMcpEnableRule(
        args.service,
        resources.GetProjectId(),
    )

    op = services_util.WaitOperation(op.name, serviceusage.GetOperationV2Beta)

    services_util.PrintOperation(op)
    log.status.Print('MCP Server enabled for service:', args.service)

