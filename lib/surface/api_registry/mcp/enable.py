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


from googlecloudsdk.calliope import base
from googlecloudsdk.core import log


# TODO(b/321801975) make command public after preview.
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.Deprecate(
    is_removed=False,  # Set to False to issue a warning first
    warning=(
        'The `gcloud alpha api-registry mcp enable` command is deprecated and '
        ' will be removed in a future release.'
    ),
    error=(
        'The `gcloud alpha api-registry mcp enable` command has been removed.'
    )
)
@base.DefaultUniverseOnly
class EnableAlpha(base.SilentCommand):
  """Enables MCP server for a given service in the current project."""

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'service',
        help='The MCP server to enable.',
    )

  def Run(self, args):
    """Enables MCP server for a given service in the current project."""
    log.status.Print(
        'MCP server enablement is no longer required. Enabling the underlying'
        ' service is now sufficient. If not already enabled, run the following'
        ' command to enable the service: gcloud alpha services enable',
        args.service,
    )


@base.ReleaseTracks(base.ReleaseTrack.BETA)
@base.Deprecate(
    is_removed=False,  # Set to False to issue a warning first
    warning=(
        'The `gcloud beta api-registry mcp enable` command is deprecated and '
        ' will be removed in a future release.'
    ),
    error=(
        'The `gcloud beta api-registry mcp enable` command has been removed.'
    )
)
@base.DefaultUniverseOnly
class EnableBeta(base.SilentCommand):
  """Enables MCP server for a given service in the current project."""

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'service',
        help='The MCP server to enable.',
    )

  def Run(self, args):
    """Enables MCP server for a given service in the current project."""
    log.status.Print(
        'MCP server enablement is no longer required. Enabling the underlying'
        ' service is now sufficient. If not already enabled, run the following'
        ' command to enable the service: gcloud beta services enable',
        args.service,
    )
