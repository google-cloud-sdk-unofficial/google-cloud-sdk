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
"""Command for listing a finding's security marks."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.scc import flags as scc_flags
from googlecloudsdk.command_lib.scc.findings import flags
from googlecloudsdk.command_lib.scc.findings import util
from googlecloudsdk.core.util import times
from googlecloudsdk.generated_clients.apis.securitycenter.v1 import securitycenter_v1_messages as messages


@base.ReleaseTracks(
    base.ReleaseTrack.GA, base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA
)
class ListMarks(base.ListCommand):
  """List a finding's security marks."""

  detailed_help = {
      "DESCRIPTION": "List a finding's security marks.",
      "EXAMPLES": """
        List all security marks for myFinding under organization 123456 and source 5678:

          $ {command} `myFinding` --organization=123456 --source=5678

        List all security marks for myFinding under project example-project and source 5678:

          $ {command} projects/example-project/sources/5678/findings/myFinding

        List all security marks for myFinding under folder 456 and source 5678:

          $ {command} folders/456/sources/5678/findings/myFinding""",
      "API REFERENCE": """
          This command uses the securitycenter/v1 API. The full documentation for
          this API can be found at: https://cloud.google.com/security-command-center""",
  }

  @staticmethod
  def Args(parser):
    # Remove URI flag.
    base.URI_FLAG.RemoveFromParser(parser)

    # Add shared flags and finding positional argument
    flags.CreateFindingArg().AddToParser(parser)
    scc_flags.PAGE_TOKEN_FLAG.AddToParser(parser)
    scc_flags.READ_TIME_FLAG.AddToParser(parser)

  def Run(self, args):
    request = messages.SecuritycenterOrganizationsSourcesFindingsListRequest()

    # Populate the request fields from args
    request.pageToken = args.page_token
    request.readTime = args.read_time
    if request.readTime:
      # Get DateTime from string and convert to the format required by the API.
      read_time_dt = times.ParseDateTime(request.readTime)
      request.readTime = times.FormatDateTime(read_time_dt)

    request = GenerateParentForListFindingsSecurityMarksCommand(
        args, request
    )
    client = apis.GetClientInstance("securitycenter", "v1")
    list_findings_response = client.organizations_sources_findings.List(request)

    # Get the security marks
    response = util.ExtractSecurityMarksFromResponse(
        list_findings_response.listFindingsResults, args
    )
    return response


def GenerateParentForListFindingsSecurityMarksCommand(args, req):
  """Generates a finding's parent and adds filter based on finding name."""
  util.ValidateMutexOnFindingAndSourceAndOrganization(args)
  finding_name = util.GetFindingNameForParent(args)
  req.parent = util.GetSourceParentFromResourceName(finding_name)
  req.filter = "name : \"" + util.GetFindingIdFromName(finding_name) + "\""
  return req
