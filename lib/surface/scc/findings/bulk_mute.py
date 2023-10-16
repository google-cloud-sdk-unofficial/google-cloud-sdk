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
"""Command to bulk mute Security Command Center findings based on a filter."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.scc.findings import util
from googlecloudsdk.generated_clients.apis.securitycenter.v1 import securitycenter_v1_messages as messages


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.ALPHA)
class BulkMute(base.Command):
  """Bulk mute Security Command Center findings based on a filter."""

  detailed_help = {
      "DESCRIPTION": (
          "Bulk mute Security Command Center findings based on a filter."
      ),
      "EXAMPLES": """
      To bulk mute findings given organization ``123'' based on a filter on category that equals ``XSS_SCRIPTING'', run:

        $ {command} --organization=organizations/123 --filter="category=\\"XSS_SCRIPTING\\""
        $ {command} --organization=123 --filter="category=\\"XSS_SCRIPTING\\""

      To bulk mute findings given folder ``123'' based on a filter on category that equals ``XSS_SCRIPTING'', run:

        $ {command} --folder=folders/123 --filter="category=\\"XSS_SCRIPTING\\""
        $ {command} --folder=123 --filter="category=\\"XSS_SCRIPTING\\""

      To bulk mute findings given project ``123'' based on a filter on category that equals ``XSS_SCRIPTING'', run:

        $ {command} --project=projects/123 --filter="category=\\"XSS_SCRIPTING\\""
        $ {command} --project=123 --filter="category=\\"XSS_SCRIPTING\\""
      """,
      "API REFERENCE": """
          This command uses the securitycenter/v1 API. The full documentation for
          this API can be found at: https://cloud.google.com/security-command-center""",
  }

  @staticmethod
  def Args(parser):
    # Create argument group for parent, this can be org | folder | project.
    parent_group = parser.add_group(mutex=True, required=True)
    parent_group.add_argument(
        "--organization",
        help="""Organization where the findings reside. Formatted as ``organizations/123'' or just ``123''.""",
    )

    parent_group.add_argument(
        "--folder",
        help="""Folder where the findings reside. Formatted as ``folders/456'' or just ``456''.""",
    )
    parent_group.add_argument(
        "--project",
        help="""Project (id or number) where the findings reside. Formatted as ``projects/789'' or just ``789''.""",
    )

    parser.add_argument(
        "--filter",
        help="The filter string which will applied to findings being muted.",
    )

  def Run(self, args):
    # Create the request and include the filter from args.
    request = messages.SecuritycenterOrganizationsFindingsBulkMuteRequest()
    request.bulkMuteFindingsRequest = messages.BulkMuteFindingsRequest()
    request.bulkMuteFindingsRequest.filter = args.filter
    request.parent = util.ValidateAndGetParent(args)
    args.filter = ""

    client = apis.GetClientInstance("securitycenter", "v1")
    result = client.organizations_findings.BulkMute(request)

    return result
