# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Command for updating interconnects."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.interconnects import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.interconnects import flags
from googlecloudsdk.command_lib.compute.interconnects.locations import flags as location_flags
from googlecloudsdk.command_lib.util.args import labels_util

_LOCATION_FLAG_MSG = (
    'The location for the interconnect. The locations can be listed by using '
    'the `{parent_command} locations list` command to find '
    'the appropriate location to use when creating an interconnect.')


def _ArgsCommon(
    cls, parser, support_labels=False, support_effective_location=False
):
  """Shared arguments for update commands."""
  cls.INTERCONNECT_ARG = flags.InterconnectArgument()
  cls.INTERCONNECT_ARG.AddArgument(parser, operation_type='update')

  parser.add_argument(
      '--description',
      help='An optional, textual description for the interconnect.',
  )
  flags.AddAdminEnabledForUpdate(parser)
  flags.AddNocContactEmail(parser)
  flags.AddRequestedLinkCountForUpdate(parser)
  if support_labels:
    labels_util.AddUpdateLabelsFlags(parser)
  if support_effective_location:
    cls.LOCATION_ARG = (
        location_flags.InterconnectLocationArgumentForOtherResource(
            _LOCATION_FLAG_MSG, required=False))
    cls.LOCATION_ARG.AddArgument(parser)


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.GA)
class UpdateGA(base.UpdateCommand):
  """Update a Compute Engine interconnect.

  *{command}* is used to update interconnects. An interconnect represents a
  single specific connection between Google and the customer.
  """

  INTERCONNECT_ARG = None
  _support_effective_location = False
  _support_labels = False

  @classmethod
  def Args(cls, parser):
    _ArgsCommon(
        cls,
        parser,
        support_labels=cls._support_labels,
        support_effective_location=cls._support_effective_location,
    )

  def Collection(self):
    return 'compute.interconnects'

  def _DoRun(self, args, support_labels=False):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    ref = self.INTERCONNECT_ARG.ResolveAsResource(args, holder.resources)
    interconnect = client.Interconnect(ref, compute_client=holder.client)

    labels = None
    label_fingerprint = None
    if support_labels:
      labels_diff = labels_util.Diff.FromUpdateArgs(args)
      if labels_diff.MayHaveUpdates():
        old_interconnect = interconnect.Describe()
        labels = labels_diff.Apply(
            holder.client.messages.Interconnect.LabelsValue,
            old_interconnect.labels).GetOrNone()
        if labels is not None:
          label_fingerprint = old_interconnect.labelFingerprint
    location = None
    if self._support_effective_location and args.IsSpecified('location'):
      location_ref = self.LOCATION_ARG.ResolveAsResource(args, holder.resources)
      location = location_ref.SelfLink()

    return interconnect.Patch(
        description=args.description,
        interconnect_type=None,
        requested_link_count=args.requested_link_count,
        link_type=None,
        admin_enabled=args.admin_enabled,
        noc_contact_email=args.noc_contact_email,
        location=location,
        labels=labels,
        label_fingerprint=label_fingerprint,
    )

  def Run(self, args):
    self._DoRun(args, support_labels=self._support_labels)


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.BETA)
class UpdateBeta(UpdateGA):
  """Update a Compute Engine interconnect.

  *{command}* is used to update interconnects. An interconnect represents a
  single specific connection between Google and the customer.
  """
  _support_effective_location = False
  _support_labels = True


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAlpha(UpdateBeta):
  """Update a Compute Engine interconnect.

  *{command}* is used to update interconnects. An interconnect represents a
  single specific connection between Google and the customer.
  """
  _support_effective_location = True
