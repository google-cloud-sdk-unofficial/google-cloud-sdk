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
"""services mcp content-security get command."""

from googlecloudsdk.calliope import base
from googlecloudsdk.core import log

_PROJECT_RESOURCE = 'projects/%s'
_CONTENT_SECURITY_POLICY_DEFAULT = '/contentSecurityPolicies/default'


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Get(base.Command):
  """Get MCP content security providers for a project.

  Get MCP content security providers for a project.

  ## EXAMPLES

  Get MCP content security providers for a project:

    $ {command}

  Get MCP content security providers for a project `my-project`:

    $ {command} --project=my-project
  """

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat("""
          table(
            contentSecurityProvider
          )
        """)

  def Run(self, args):
    """Run command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The content security providers for a project.
    """

    log.warning(
        'This command is not required. Please use gcloud model-armor'
        ' floorsettings describe instead and get the floor settings.'
    )
    return None
