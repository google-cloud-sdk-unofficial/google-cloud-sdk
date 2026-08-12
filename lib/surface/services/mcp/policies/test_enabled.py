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
"""services mcp policies test-enabled command."""
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
class TestEnabled(base.Command):
  """Test a service against the result of merging MCP policies in the resource hierarchy.

  Test a service against the result of merging MCP policies in the resource
  hierarchy.

  ## EXAMPLES

  Test for service my-service for current project:

    $ {command} my-service

  Test for service my-service for project `my-project`:

    $ {command} my-service --project=my-project
  """

  @staticmethod
  def Args(parser):
    common_flags.add_resource_args(parser)
    parser.add_argument(
        'service', help='Name of the service. example: foobar.googleapis.com'
    )

  def Run(self, args):
    """Run command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The enablement of the given service.
    """
    pass
