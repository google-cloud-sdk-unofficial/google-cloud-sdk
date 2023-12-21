# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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

"""Command to Get a Cloud Security Command Center mute config."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.api_lib.scc import securitycenter_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.scc import flags as scc_flags
from googlecloudsdk.command_lib.scc import util as scc_util
from googlecloudsdk.command_lib.scc.muteconfigs import flags
from googlecloudsdk.command_lib.scc.muteconfigs import util
from googlecloudsdk.core import properties


# TODO: b/308476775 - Migrate Get command usage to Describe
@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.ALPHA)
class Get(base.Command):
  """Get a Cloud Security Command Center mute config."""

  detailed_help = {
      "DESCRIPTION": "Get a Cloud Security Command Center mute config.",
      "EXAMPLES": """
        To get a mute config given organization ``123'' with id ``my-test-mute-config'', run:

        $ {command} my-test-mute-config --organization=organizations/123
        $ {command} my-test-mute-config --organization=123
        $ {command} organizations/123/muteConfigs/my-test-mute-config

      To get a mute config given folder ``456'' with id ``my-test-mute-config'', run:

        $ {command} my-test-mute-config --folder=folders/456
        $ {command} my-test-mute-config --folder=456
        $ {command} folders/456/muteConfigs/my-test-mute-config

      To get a mute config given project ``789'' with id ``my-test-mute-config'', run:

        $ {command} my-test-mute-config --project=projects/789
        $ {command} my-test-mute-config --project=789
        $ {command} projects/789/muteConfigs/my-test-mute-config""",
      "API REFERENCE": """
        This command uses the securitycenter/v1 API. The full documentation for
        this API can be found at: https://cloud.google.com/security-command-center""",
  }

  @staticmethod
  def Args(parser):
    # Add flags and positional arguments.
    flags.MUTE_CONFIG_FLAG.AddToParser(parser)
    flags.AddParentGroup(parser)
    # TODO: b/311713896 - Remove api-version flag when v2 is fully GA.
    scc_flags.API_VERSION_FLAG.AddToParser(parser)
    scc_flags.LOCATION_FLAG.AddToParser(parser)
    parser.display_info.AddFormat(properties.VALUES.core.default_format.Get())

  def Run(self, args):
    # Determine what version to call from --location and --api-version.
    version = scc_util.GetVersionFromArguments(args, args.mute_config)
    messages = securitycenter_client.GetMessages(version)
    request = messages.SecuritycenterOrganizationsMuteConfigsGetRequest()

    # Generate name and send request if the user continues.
    request = util.GenerateMuteConfigName(args, request, version)
    client = securitycenter_client.GetClient(version)

    response = client.organizations_muteConfigs.Get(request)
    return response
