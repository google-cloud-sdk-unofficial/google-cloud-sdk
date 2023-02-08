# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""The command to update Config Management Feature."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.container.fleet import resources
from googlecloudsdk.command_lib.container.fleet.features import base


class Delete(base.UpdateCommand):
  """Remove the Identity Service Feature Spec for the given membership.

  Removes the Identity Service Feature Spec for the given
  membership.

  ## EXAMPLES

  To delete an Identity Service configuration for a membership, run:

    $ {command} --membership=MEMBERSHIP_NAME
  """

  feature_name = 'identityservice'

  _fleet_default_member_config_supported_tracks = [
      calliope_base.ReleaseTrack.ALPHA, calliope_base.ReleaseTrack.BETA
  ]

  @classmethod
  def Args(cls, parser):
    resources.AddMembershipResourceArg(
        parser, membership_help='Membership name provided during registration.')

    if cls.ReleaseTrack(
    ) not in cls._fleet_default_member_config_supported_tracks:
      return

    parser.add_argument(
        '--fleet-default-member-config',
        action='store_true',
        help="""If specified, deletes the default membership
        configuration present in your fleet.

        To delete the default membership configuration present in your
        fleet, run:

          $ {command} --fleet-default-member-config""",
    )

  def Run(self, args):
    update_mask = []
    patch = self.messages.Feature()

    if self.ReleaseTrack(
    ) in self._fleet_default_member_config_supported_tracks:
      # Clear the fleet_default_member_config if the
      # fleet_default_member_config flag is set to true.
      if args.fleet_default_member_config:
        self._UpdateFleetDefaultMemberConfigMaskAndPatch(update_mask, patch)
        # If the user only specified fleet_default_member_config flag,
        # stop further processing.
        if not args.membership:
          self.Update(update_mask, patch)
          return

    self._UpdateMembershipSpecsMaskAndPatch(args, update_mask, patch)
    # Patch the feature based on the given masks.
    self.Update(update_mask, patch)

  def _UpdateFleetDefaultMemberConfigMaskAndPatch(self, mask, patch):
    patch.fleetDefaultMemberConfig = self.messages.CommonFleetDefaultMemberConfigSpec(
    )
    mask.append('fleet_default_member_config')

  def _UpdateMembershipSpecsMaskAndPatch(self, args, mask, patch):
    # Get fleet memberships (cluster registered with fleet) from GCP Project.
    membership = base.ParseMembership(
        args, prompt=True, autoselect=True, search=True)

    # Setup a patch to set the MembershipSpec to the empty proto ("delete").
    specs = {membership: self.messages.MembershipFeatureSpec()}
    patch.membershipSpecs = self.hubclient.ToMembershipSpecs(specs)
    mask.append('membership_specs')
