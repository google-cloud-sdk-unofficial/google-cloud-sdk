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
"""Command for compute reservations update."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import request_helper
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.reservations import flags as r_flags
from googlecloudsdk.command_lib.compute.reservations import resource_args
from googlecloudsdk.command_lib.compute.reservations import util


def _ValidateArgs(args, support_share_with):
  """Validates that both share settings arguments are mentioned.

  Args:
    args: The arguments given to the update command.
    support_share_with: Check the version.
  """
  # Check the vesrion and share-with option.
  share_with = False
  parameter_names = ['--share-with', '--vm-count']
  one_option_exception_message = (
      'Please provide one of these options: 1- specify '
      'share-with to update the project list. 2- specify '
      'reservation vm-count to resize. ')
  all_options_exception_message = ('Please provide only one of these options: '
                                   '1- specify share-with to update the project'
                                   ' list. 2- specify reservation vm-count to '
                                   'resize. ')
  if support_share_with:
    if args.IsSpecified('share_with'):
      share_with = True
  # For GA only check the size.
  if not support_share_with and not args.IsSpecified('vm_count'):
    raise exceptions.MinimumArgumentException(parameter_names,
                                              one_option_exception_message)

  # For Beta and alpha check both.
  if not share_with and not args.IsSpecified('vm_count'):
    raise exceptions.MinimumArgumentException(parameter_names,
                                              one_option_exception_message)

  if share_with and args.IsSpecified('vm_count'):
    parameter_names = ['--share-with', '--vm-count']
    raise exceptions.OneOfArgumentsRequiredException(
        parameter_names, all_options_exception_message)


def _GetShareSettingUpdateRequest(args, reservation_ref, holder):
  """Create Update Request for share-with.

  Returns:
  update request.
  Args:
   args: The arguments given to the update command.
   reservation_ref: reservation refrence.
   holder: base_classes.ComputeApiHolder.
  """
  messages = holder.client.messages
  # Set updated properties and build update mask.
  update_mask = []
  share_settings = None
  share_settings = util.MakeShareSettingsWithArgs(messages, args, 'projects')
  update_mask.append('shareSettings.projects')

  # Build reservation object using new share-settings.
  r_resource = util.MakeReservationMessage(messages, reservation_ref.Name(),
                                           share_settings, None, None,
                                           reservation_ref.zone)
  # Build update request.
  r_update_request = messages.ComputeReservationsUpdateRequest(
      reservation=reservation_ref.Name(),
      reservationResource=r_resource,
      paths=update_mask,
      project=reservation_ref.project,
      zone=reservation_ref.zone)

  return r_update_request


def _GetResizeRequest(args, reservation_ref, holder):
  """Create Update Request for vm_count.

  Returns:
  resize request.
  Args:
   args: The arguments given to the update command.
   reservation_ref: reservation refrence.
   holder: base_classes.ComputeApiHolder.
  """
  messages = holder.client.messages
  vm_count = None
  if args.IsSpecified('vm_count'):
    vm_count = args.vm_count

  # Build resize request.
  r_resize_request = messages.ComputeReservationsResizeRequest(
      reservation=reservation_ref.Name(),
      reservationsResizeRequest=messages.ReservationsResizeRequest(
          specificSkuCount=vm_count),
      project=reservation_ref.project,
      zone=reservation_ref.zone)

  return r_resize_request


def _RunUpdate(holder, args, support_share_with=False):
  """Common routine for updating reservation."""
  resources = holder.resources
  service = holder.client.apitools_client.reservations

  # Validate the command.
  _ValidateArgs(args, support_share_with)
  reservation_ref = resource_args.GetReservationResourceArg().ResolveAsResource(
      args,
      resources,
      scope_lister=compute_flags.GetDefaultScopeLister(holder.client))

  result = list()
  errors = []
  share_with = False
  if support_share_with:
    if args.IsSpecified('share_with'):
      share_with = True

  if support_share_with and share_with:
    r_update_request = _GetShareSettingUpdateRequest(args, reservation_ref,
                                                     holder)
    # Invoke Reservation.update API.
    result.append(
        list(
            request_helper.MakeRequests(
                requests=[(service, 'Update', r_update_request)],
                http=holder.client.apitools_client.http,
                batch_url=holder.client.batch_url,
                errors=errors)))
    if errors:
      utils.RaiseToolException(errors)

  if args.IsSpecified('vm_count'):
    r_resize_request = _GetResizeRequest(args, reservation_ref, holder)
    # Invoke Reservation.resize API.
    result.append(
        holder.client.MakeRequests(([(service, 'Resize', r_resize_request)])))

  return result


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  """Update Compute Engine reservations."""
  _support_share_with = False

  @classmethod
  def Args(cls, parser):
    resource_args.GetReservationResourceArg().AddArgument(
        parser, operation_type='update')
    r_flags.GetVmCountFlag(False).AddToParser(parser)

  def Run(self, args):
    """Common routine for updating reservation."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    resources = holder.resources
    service = holder.client.apitools_client.reservations

    # Validate the command.
    _ValidateArgs(args, self._support_share_with)
    reservation_ref = resource_args.GetReservationResourceArg(
    ).ResolveAsResource(
        args,
        resources,
        scope_lister=compute_flags.GetDefaultScopeLister(holder.client))

    result = list()
    errors = []
    share_with = False
    if self._support_share_with:
      if args.IsSpecified('share_with'):
        share_with = True

    if self._support_share_with and share_with:
      r_update_request = _GetShareSettingUpdateRequest(args, reservation_ref,
                                                       holder)
      # Invoke Reservation.update API.
      result.append(
          list(
              request_helper.MakeRequests(
                  requests=[(service, 'Update', r_update_request)],
                  http=holder.client.apitools_client.http,
                  batch_url=holder.client.batch_url,
                  errors=errors)))
      if errors:
        utils.RaiseToolException(errors)

    if args.IsSpecified('vm_count'):
      r_resize_request = _GetResizeRequest(args, reservation_ref, holder)
      # Invoke Reservation.resize API.
      result.append(
          holder.client.MakeRequests(([(service, 'Resize', r_resize_request)])))

    return result


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class UpdateBeta(Update):
  """Update Compute Engine reservations."""
  _support_share_with = True

  @classmethod
  def Args(cls, parser):
    resource_args.GetReservationResourceArg().AddArgument(
        parser, operation_type='update')
    r_flags.GetShareWithFlag().AddToParser(parser)
    r_flags.GetVmCountFlag(False).AddToParser(parser)


Update.detailed_help = {
    'EXAMPLES':
        """
        To update a given Compute Enginer reservation with 500 VM instances, run:

            $ {command} my-reservation --zone=ZONE --vm-count=500
        """
}

UpdateBeta.detailed_help = {
    'EXAMPLES':
        """
        To update project list of a Compute Engine reservation ``my-reservation''  in Zone: ``us-central1-a'', run:

            $ {command} my-reservation --share-with=123 --zone=us-central1-a

        To update a given Compute Enginer reservation with 500 VM instances, run:

            $ {command} my-reservation --zone=ZONE --vm-count=500
        """
}
