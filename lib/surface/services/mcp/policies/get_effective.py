# -*- coding: utf-8 -*- #
# Copyright 2025 Google Inc. All Rights Reserved.
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

# TODO: b/300099033 - Capitalize and turn into a sentence.
"""services MCP policies get-effective-policy command."""

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.services import common_flags


# TODO: b/321801975 - Make command public after suv2 launch.
@base.Deprecate(
    is_removed=False,
    warning='MCP policies are not required and this command is no-op.',
    error='MCP policies are not required and this command is no-op.',
)
@base.UniverseCompatible
@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class GetEffectivePolicy(base.Command):
  """Get effective MCP policy for a project, folder or organization.

  Get effective MCP policy for a project, folder or organization.

  ## EXAMPLES

   Get effective MCP policy for the current project:

   $ {command}

   Get effective MCP policy for project `my-project`:

   $ {command} --project=my-project
  """

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--view',
        help=(
            'The view of the effective MCP policy. BASIC includes basic'
            ' metadata about the effective MCP policy. FULL includes every'
            ' information related to effective MCP policy.'
        ),
        choices=['BASIC', 'FULL'],
        default='BASIC',
    )
    common_flags.add_resource_args(parser)

    parser.display_info.AddFormat("""
          table(
            EnabledMcpService:label=EnabledMcpService:sort=1,
            EnabledMcpPolicies:label=EnabledMcpPolicies
          )
        """)

  def Run(self, args):
    """Run command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Effective Policy.
    """
    pass
