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
"""services mcp policies get command."""

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.services import common_flags


# TODO(b/321801975) make command public after suv2 launch.
@base.Deprecate(
    is_removed=False,
    warning='MCP policies are not required and this command is no-op.',
    error='MCP policies are not required and this command is no-op.',
)
@base.UniverseCompatible
@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Get(base.Command):
  """Get MCP policy for a project, folder or organization.

  Get MCP policy for a project, folder or
  organization.

  ## EXAMPLES

   Get MCP policy for default policy on current project:

   $ {command}
      OR
   $ {command} --policy-name=default

   Get MCP policy for default policy on current project and save the
   content in an output file:

   $ {command} --output-file=/path/to/the/file.yaml
       OR
   $ {command} --output-file=/path/to/the/file.json
  """

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--policy-name',
        help='Name of the MCP policy. Currently only "default" is supported.',
        default='default',
    )
    common_flags.add_resource_args(parser)

    parser.add_argument(
        '--output-file',
        help=(
            'Path to the file to write policy contents to. Supported format:'
            '.yaml or .json.'
        ),
    )

  def Run(self, args):
    """Run command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Resource name and its parent name.
    """
    pass
