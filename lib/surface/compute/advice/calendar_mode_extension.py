# -*- coding: utf-8 -*- #
# Copyright 2026 Google LLC. All Rights Reserved.
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
"""Command for advising on extending a future reservation in calendar mode."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.advice import flags
from googlecloudsdk.command_lib.compute.future_reservations import resource_args
from googlecloudsdk.core.util import times

DETAILED_HELP = {
    "DESCRIPTION": (
        """
      Get advice on the optimal end time for extending a future reservation.

      Use this command to verify whether extending an existing future reservation is possible and get a recommendation based on the current available capacity.
    """
    ),
    "EXAMPLES": (
        """
      To check whether extending an existing future reservation until the desired date is possible, run the following command:

        $ {command} my-future-reservation \
            --end-time=2026-08-30T00:00:00Z \
            --zone=us-central1-a
      """
    ),
}


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.Hidden
class CalendarModeExtension(base.Command):
  """Get advice on the optimal end time for extending a future reservation."""

  detailed_help = DETAILED_HELP
  category = base.COMPUTE_CATEGORY

  _FR_ARG = resource_args.GetFutureReservationResourceArg()

  @classmethod
  def Args(cls, parser):
    """Adds arguments for the calendar-mode-extension command to a parser."""
    cls._FR_ARG.AddArgument(parser, operation_type="get extension advice for")
    flags.AddEndTimeFlag(parser)

  def Run(self, args):
    """Runs the calendar-mode-extension command."""

    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    messages = client.messages
    resources = holder.resources

    fr_resource = self._FR_ARG.ResolveAsResource(
        args,
        resources,
    )

    project = fr_resource.project
    zone = fr_resource.zone
    region = utils.ZoneNameToRegionName(zone)
    end_time = times.FormatDateTime(args.end_time)

    inner_request = messages.CalendarModeExtensionAdviceRequest(
        endTimeNotLaterThan=end_time,
        futureReservation=fr_resource.RelativeName(),
    )

    outer_request = messages.ComputeAdviceCalendarModeExtensionRequest(
        calendarModeExtensionAdviceRequest=inner_request,
        project=project,
        region=region,
    )

    return client.apitools_client.advice.CalendarModeExtension(outer_request)
