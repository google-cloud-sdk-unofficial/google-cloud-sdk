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

"""api registry mcp server disable command."""

from googlecloudsdk.api_lib.api_registry import resources
from googlecloudsdk.api_lib.services import services_util
from googlecloudsdk.api_lib.services import serviceusage
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log


# TODO(b/321801975) make command public after preview.
@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class DisableAlpha(base.SilentCommand):
  """Disables MCP server for a given service in the current project."""

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'service',
        help='The MCP server to disable.',
    )

  def Run(self, args):
    """Disables MCP server for a given service in the current project."""
    op = serviceusage.RemoveMcpEnableRule(
        resources.GetProjectId(),
        args.service,
    )

    if op is None:
      return None

    services_util.WaitOperation(op.name, serviceusage.GetOperationV2Beta)

    # services_util.PrintOperation(op)
    log.status.Print('MCP Server disabled for service:', args.service)


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.BETA)
class DisableBeta(base.SilentCommand):
  """Disables MCP server for a given service in the current project."""

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'service',
        help='The MCP server to disable.',
    )

  def Run(self, args):
    """Disables MCP server for a given service in the current project."""
    op = serviceusage.RemoveMcpEnableRule(
        resources.GetProjectId(),
        args.service,
    )

    if op is None:
      return None

    services_util.WaitOperation(op.name, serviceusage.GetOperationV2Beta)

    # services_util.PrintOperation(op)
    log.status.Print('MCP Server disabled for service:', args.service)
