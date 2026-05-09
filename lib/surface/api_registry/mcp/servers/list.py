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

"""Command to List MCP servers."""

from googlecloudsdk.api_lib.api_registry import utils
from googlecloudsdk.api_lib.api_registry.mcp import servers
from googlecloudsdk.calliope import base


_DETAILED_HELP = {
    'DESCRIPTION':
        '{description}',
    'EXAMPLES':
        """ \
        To list all MCP servers in a project, run:

          $ {command}
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.Deprecate(
    is_removed=False,  # Set to False to issue a warning first
    warning=(
        'The `gcloud alpha api-registry mcp servers list` command is deprecated'
        ' and will be removed in a future release. Please use `gcloud alpha'
        ' agent-registry mcp-servers list` instead. Note: Agent Registry only'
        ' lists MCP servers for service APIs that are enabled in a project. For'
        ' more information, see: '
        'https://docs.cloud.google.com/sdk/gcloud/reference/alpha/agent-registry/mcp-servers'
    ),
    error=(
        'The `gcloud alpha api-registry mcp servers list` command has been'
        ' removed. Please use `gcloud alpha agent-registry mcp-servers list`'
        ' instead. For more information, see: '
        'https://docs.cloud.google.com/sdk/gcloud/reference/alpha/agent-registry/mcp-servers'
    )
)
@base.DefaultUniverseOnly
class ListAlpha(base.ListCommand):
  """List MCP servers."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat('json')
    parser.add_argument(
        '--all',
        action='store_true',
        help='If provided, list all the available (both enabled and'
        ' non-enabled) MCP servers for the project.',
    )

  def Run(self, args):
    """Run the list command."""
    client = servers.McpServersClient(version='v1alpha')
    project = utils.GetProject()
    location = utils.GetLocation()
    parent = (
        f'projects/{project}/locations/{location}'
    )
    return client.ListAlpha(parent, args)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
@base.Deprecate(
    is_removed=False,  # Set to False to issue a warning first
    warning=(
        'The `gcloud beta api-registry mcp servers list` command is deprecated'
        ' and will be removed in a future release. Please use `gcloud alpha'
        ' agent-registry mcp-servers list` instead. Note: Agent Registry only'
        ' lists MCP servers for service APIs that are enabled in a project. For'
        ' more information, see: '
        'https://docs.cloud.google.com/sdk/gcloud/reference/alpha/agent-registry/mcp-servers'
    ),
    error=(
        'The `gcloud beta api-registry mcp servers list` command has been'
        ' removed. Please use `gcloud alpha agent-registry mcp-servers list`'
        ' instead. For more information, see: '
        'https://docs.cloud.google.com/sdk/gcloud/reference/alpha/agent-registry/mcp-servers'
    )
)
@base.DefaultUniverseOnly
class ListBeta(base.ListCommand):
  """List MCP servers."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat('json')
    parser.add_argument(
        '--all',
        action='store_true',
        help='If provided, list all the available (both enabled and'
        ' non-enabled) MCP servers for the project.',
    )

  def Run(self, args):
    """Run the list command."""
    client = servers.McpServersClient(version='v1beta')
    project = utils.GetProject()
    location = utils.GetLocation()
    parent = (
        f'projects/{project}/locations/{location}'
    )
    return client.ListBeta(parent, args)
