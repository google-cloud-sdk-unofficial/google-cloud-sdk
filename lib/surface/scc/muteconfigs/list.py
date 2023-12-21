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
"""Command to List a Cloud Security Command Center mute config."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.scc import securitycenter_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.scc import flags as scc_flags
from googlecloudsdk.command_lib.scc import util as scc_util
from googlecloudsdk.command_lib.scc.muteconfigs import flags
from googlecloudsdk.command_lib.scc.muteconfigs import util


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List Cloud Security Command Center mute configs."""

  detailed_help = {
      "DESCRIPTION": "List Cloud Security Command Center mute configs.",
      "EXAMPLES": """
        List mute configs under organization ``123'':

        $ {command} --organization=organizations/123
        $ {command} --organization=123

      List mute configs under folder ``456'':

        $ {command} --folder=folders/456
        $ {command} --folder=456

      List mute configs under project ``789'':

        $ {command} --project=projects/789
        $ {command} --project=789""",
      "API REFERENCE": """
        This command uses the securitycenter/v1 API. The full documentation for
        this API can be found at: https://cloud.google.com/security-command-center""",
  }

  @staticmethod
  def Args(parser):
    # Remove URI flag. This flag is added from base.ListCommand and is not
    # needed for this command.
    base.URI_FLAG.RemoveFromParser(parser)
    # Add flags and positional arguments
    flags.AddParentGroup(parser, True)
    # TODO: b/311713896 - Remove api-version flag when v2 is fully GA.
    scc_flags.API_VERSION_FLAG.AddToParser(parser)
    scc_flags.LOCATION_FLAG.AddToParser(parser)

  def Run(self, args):
    # Determine what version to call from --location and --api-version.
    version = scc_util.GetVersionFromArguments(args)
    # Build request from args.
    messages = securitycenter_client.GetMessages(version)
    request = messages.SecuritycenterOrganizationsMuteConfigsListRequest()
    request.parent = util.ValidateAndGetParent(args)
    if version == "v2":
      request.parent = util.ValidateAndGetRegionalizedParent(
          args, request.parent
      )
    client = securitycenter_client.GetClient(version)

    # Automatically handle pagination. All muteconfigs are returned regarldess
    # of --page-size argument.
    return list_pager.YieldFromList(
        client.organizations_muteConfigs,
        request,
        batch_size_attribute="pageSize",
        batch_size=args.page_size,
        field="muteConfigs",
    )
