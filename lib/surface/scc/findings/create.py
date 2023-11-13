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
"""Command for creating a Cloud Security Command Center Finding."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.api_lib.scc import securitycenter_client as sc_client
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.scc.findings import flags
from googlecloudsdk.command_lib.scc.findings import util
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import times
from googlecloudsdk.generated_clients.apis.securitycenter.v1 import securitycenter_v1_messages as scc_messages


@base.ReleaseTracks(
    base.ReleaseTrack.GA, base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA
)
class Create(base.CreateCommand):
  """Create a Cloud Security Command Center finding."""

  detailed_help = {
      "DESCRIPTION": "Create a Cloud Security Command Center finding.",
      "EXAMPLES": f"""
          Create an ACTIVE myFinding with category: XSS_SCRIPTING attached to example-project under organization 123456 and source 5678:

          $ {{command}} `myFinding` --organization=123456 --source=5678 --state=ACTIVE --category='XSS_SCRIPTING' --event-time=2023-01-11T07:00:06.861Z --resource-name='//cloudresourcemanager.{properties.VALUES.core.universe_domain.Get()}/projects/example-project'

          Create an ACTIVE myFinding attached to example-project under project example-project and source 5678:

            $ {{command}} projects/example-project/sources/5678/findings/myFinding --state=ACTIVE --category='XSS_SCRIPTING' --event-time=2023-01-11T07:00:06.861Z --resource-name='//cloudresourcemanager.{properties.VALUES.core.universe_domain.Get()}/projects/example-project'

          Create an ACTIVE myFinding attached to example-project under folder 456 and source 5678:

            $ {{command}} folders/456/sources/5678/findings/myFinding --state=ACTIVE --category='XSS_SCRIPTING' --event-time=2023-01-11T07:00:06.861Z --resource-name='//cloudresourcemanager.{properties.VALUES.core.universe_domain.Get()}/projects/example-project'""",
      "API REFERENCE": """
          This command uses the securitycenter/v1 API. The full documentation for
          this API can be found at: https://cloud.google.com/security-command-center""",
  }

  @staticmethod
  def Args(parser):
    # Add shared flags and finding positional argument.
    flags.CreateFindingArg().AddToParser(parser)
    flags.EXTERNAL_URI_FLAG.AddToParser(parser)
    flags.SOURCE_PROPERTIES_FLAG.AddToParser(parser)
    flags.STATE_FLAG.AddToParser(parser)
    flags.EVENT_TIME_FLAG_REQUIRED.AddToParser(parser)

    parser.add_argument(
        "--category",
        help="""
        Taxonomy group within findings from a given source. Example: XSS_SCRIPTING
        """,
        required=True,
    )

    parser.add_argument(
        "--resource-name",
        help="""
        Full resource name of the Google Cloud Platform resource this finding is for.
        """,
        required=True,
    )

  def Run(self, args):
    request = (
        scc_messages.SecuritycenterOrganizationsSourcesFindingsCreateRequest()
    )
    request.finding = scc_messages.Finding()
    request.finding.externalUri = args.external_uri
    if args.source_properties:
      request.finding.sourceProperties = flags.ConvertSourceProperties(
          args.source_properties
      )

    # Convert state input to scc_messages.Finding.StateValueValuesEnum object.
    request.finding.state = util.ConvertStateInput(args.state)

    # Convert event_time argument to correct format.
    event_time_dt = times.ParseDateTime(args.event_time)
    request.finding.eventTime = times.FormatDateTime(event_time_dt)

    request.finding.category = args.category
    request.finding.resourceName = args.resource_name

    request = _GenerateRequestArgumentsForCreateCommand(args, request)
    client = apis.GetClientInstance("securitycenter", "v1")
    response = client.organizations_sources_findings.Create(request)
    log.status.Print("Created.")
    return response


def _GenerateRequestArgumentsForCreateCommand(args, req):
  """Generate a finding's name, finding ID and parent using org, source and finding.

  Args:
    args: (argparse namespace)
    req: request

  Returns:
    req: Modified request
  """
  util.ValidateMutexOnFindingAndSourceAndOrganization(args)
  finding_name = util.GetFindingNameForParent(args)
  req.parent = util.GetSourceParentFromResourceName(finding_name)
  req.findingId = util.GetFindingIdFromName(finding_name)
  messages = sc_client.GetMessages()
  if not req.finding:
    req.finding = messages.Finding()
  req.finding.name = finding_name
  return req
