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
"""Command to Update a Cloud Security Command Center finding."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime

from googlecloudsdk.api_lib.scc import securitycenter_client as sc_client
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.scc import util as scc_util
from googlecloudsdk.command_lib.scc.findings import flags
from googlecloudsdk.command_lib.scc.findings import util
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import times
from googlecloudsdk.generated_clients.apis.securitycenter.v1 import securitycenter_v1_messages as messages


@base.ReleaseTracks(
    base.ReleaseTrack.GA, base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA
)
class Update(base.UpdateCommand):
  """Update a Cloud Security Command Center finding."""

  detailed_help = {
      "DESCRIPTION": "Update a Cloud Security Command Center finding.",
      "EXAMPLES": """
        Update myFinding's state from ACTIVE to INACTIVE:

          $ {command} `myFinding` --organization=123456 --source=5678 --state=INACTIVE

        Update myFinding's state from ACTIVE to INACTIVE using project name for example-project:

          $ {command} projects/example-project/sources/5678/findings/myFinding --state=INACTIVE

        Update myFinding's state from ACTIVE to INACTIVE using folder name 456:

          $ {command} folders/456/sources/5678/findings/myFinding --state=INACTIVE

        Override all source properties on myFinding:

          $ {command} `myFinding` --organization=123456 --source=5678 --source-properties="propKey1=propVal1,propKey2=propVal2"

        Selectively update a specific source property on myFinding:

          $ {command} `myFinding` --organization=123456 --source=5678 --source-properties="propKey1=propVal1,propKey2=propVal2" --update-mask="source_properties.propKey1" """,
      "API REFERENCE": """
          This command uses the securitycenter/v1 API. The full documentation for
          this API can be found at: https://cloud.google.com/security-command-center""",
  }

  @staticmethod
  def Args(parser):
    # Add flags and finding positional argument.
    flags.CreateFindingArg().AddToParser(parser)
    flags.EVENT_TIME_FLAG_NOT_REQUIRED.AddToParser(parser)
    flags.EXTERNAL_URI_FLAG.AddToParser(parser)
    flags.SOURCE_PROPERTIES_FLAG.AddToParser(parser)
    flags.STATE_FLAG.AddToParser(parser)

    parser.add_argument(
        "--update-mask",
        help="""
        Optional: If left unspecified (default), an update-mask is automatically created using the
        flags specified in the command and only those values are updated.
        For example: --external-uri='<some-uri>' --event-time='<some-time>' would automatically
        generate --update-mask='external_uri,event_time'. Note that as a result, only external-uri
        and event-time are updated for the given finding and everything else remains untouched. If
        you want to delete attributes/properties (that are not being changed in the update command)
        use an empty update-mask (''). That will delete all the mutable properties/attributes that
        aren't specified as flags in the update command. In the above example it would delete
        source-properties. State can be toggled from ACTIVE to INACTIVE and vice-versa but it cannot
        be deleted.""",
    )
    parser.display_info.AddFormat(properties.VALUES.core.default_format.Get())

  def Run(self, args):
    request = messages.SecuritycenterOrganizationsSourcesFindingsPatchRequest()
    request.updateMask = args.update_mask

    # Create update mask if none was specified. The API supports both snake
    # and camel casing. To pass the existing tests we map the arguments from
    # kebab casing to camel casing in the 'mutable_fields' dict.
    if not args.update_mask:
      mutable_fields = {
          "--event-time": "eventTime",
          "--external-uri": "externalUri",
          "--source-properties": "sourceProperties",
          "--state": "state",
      }
      request.updateMask = ""
      for arg in args.GetSpecifiedArgNames():
        if arg in mutable_fields:
          request.updateMask += "," + mutable_fields[arg]

      # Delete the first character of the update mask if it is a comma.
      if request.updateMask.startswith(","):
        request.updateMask = request.updateMask[1:]

    request.finding = messages.Finding()

    request.finding.externalUri = args.external_uri
    if args.source_properties:
      request.finding.sourceProperties = flags.ConvertSourceProperties(
          args.source_properties
      )
    request.finding.state = util.ConvertStateInput(args.state)

    request.name = GenerateFindingName(args)
    request.updateMask = scc_util.CleanUpUserMaskInput(request.updateMask)
    request = UpdateEventTime(args, request)
    client = apis.GetClientInstance("securitycenter", "v1")
    response = client.organizations_sources_findings.Patch(request)
    log.status.Print("Updated.")
    return response


def GenerateFindingName(args):
  """Generate a finding's name using org, source and finding id."""
  util.ValidateMutexOnFindingAndSourceAndOrganization(args)
  return util.GetFindingNameForParent(args)


def UpdateEventTime(args, req):
  """Process and include the event time of a finding."""
  # Convert event_time argument to correct format.
  if args.event_time:
    event_time_dt = times.ParseDateTime(args.event_time)
    req.finding.eventTime = times.FormatDateTime(event_time_dt)

  # All requests require an event time.
  if args.event_time is None:
    # Get current utc time and convert to a string representation.
    event_time = datetime.datetime.now(tz=datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%S.%fZ"
    )
    if req.finding is None:
      req.finding = sc_client.GetMessages().Finding()
    req.finding.eventTime = event_time
    req.updateMask = req.updateMask + ",event_time"
  return req
