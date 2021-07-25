# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Command for compute future reservations update."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import request_helper
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.future_reservations import flags as fr_flags
from googlecloudsdk.command_lib.compute.future_reservations import util


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Update(base.UpdateCommand):
  """Update Compute Engine future reservations."""

  fr_arg = None

  detailed_help = {
      'EXAMPLES':
          """
        To update total count, start and end time of a Compute Engine future reservation in ``us-central1-a'', run:

            $ {command} my-future-reservation --total-count=1000 --start-time=2021-11-10T07:00:00Z
          --end-time=2021-12-10T07:00:00Z --zone=us-central1-a
        """
  }

  @classmethod
  def Args(cls, parser):
    cls.fr_arg = compute_flags.ResourceArgument(
        resource_name='future reservation',
        plural=False,
        name='FUTURE_RESERVATION',
        zonal_collection='compute.futureReservations',
        zone_explanation=compute_flags.ZONE_PROPERTY_EXPLANATION,
    )

    cls.fr_arg.AddArgument(parser, operation_type='update')
    fr_flags.GetTotalCountFlag(required=False).AddToParser(parser)
    fr_flags.GetStartTimeFlag(required=False).AddToParser(parser)

    scope = parser.add_mutually_exclusive_group()
    scope.add_argument('--end-time', help=fr_flags.GetEndTimeHelpText())
    scope.add_argument(
        '--duration', type=int, help=fr_flags.GetDurationHelpText())

  def _ValidateArgs(self, args):
    """Validates that at least one field to update is specified.

    Args:
      args: The arguments given to the update command.
    """

    if not (args.IsSpecified('total_count') or args.IsSpecified('start_time') or
            args.IsSpecified('end_time') or args.IsSpecified('duration')):
      parameter_names = [
          '--total-count', '--start-time', '--end-time', '--duration'
      ]
      raise exceptions.MinimumArgumentException(
          parameter_names, 'Please specify at least one property to update')

  def Run(self, args):
    self._ValidateArgs(args)
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    resources = holder.resources
    fr_ref = self.fr_arg.ResolveAsResource(
        args,
        resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client))

    messages = holder.client.messages
    service = holder.client.apitools_client.futureReservations

    # Set updated properties and build update mask.
    update_mask = []
    sku_properties = messages.FutureReservationSpecificSKUProperties()

    if args.IsSpecified('total_count'):
      sku_properties = util.MakeSpecificSKUPropertiesMessage(
          messages, None, total_count=args.total_count)
      update_mask.append('specificSkuProperties.totalCount')

    start_time = None
    if args.IsSpecified('start_time'):
      start_time = args.start_time
      update_mask.append('timeWindow.startTime')

    end_time = None
    if args.IsSpecified('end_time'):
      end_time = args.end_time
      update_mask.append('timeWindow.endTime')

    duration = None
    if args.IsSpecified('duration'):
      duration = args.duration
      update_mask.append('timeWindow.duration')

    time_window = util.MakeTimeWindowMessage(messages, start_time, end_time,
                                             duration)

    # Build future reservation object using new properties.
    fr_resource = messages.FutureReservation(
        name=fr_ref.Name(),
        specificSkuProperties=sku_properties,
        timeWindow=time_window)

    # Build update request.
    fr_update_request = messages.ComputeFutureReservationsUpdateRequest(
        futureReservation=fr_ref.Name(),
        futureReservationResource=fr_resource,
        paths=update_mask,
        project=fr_ref.project,
        zone=fr_ref.zone)

    # Invoke futureReservation.update API.
    errors = []
    result = list(
        request_helper.MakeRequests(
            requests=[(service, 'Update', fr_update_request)],
            http=holder.client.apitools_client.http,
            batch_url=holder.client.batch_url,
            errors=errors))
    if errors:
      utils.RaiseToolException(errors)
    return result
