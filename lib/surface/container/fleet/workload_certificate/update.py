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
"""The command to update Workload Certificate Feature."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as gbase
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.container.fleet.features import base
from googlecloudsdk.core import exceptions
from googlecloudsdk.core.console import console_io


@gbase.ReleaseTracks(gbase.ReleaseTrack.ALPHA)
class Update(base.UpdateCommand):
  """Update the configuration of the Workload Certificate Feature.

  Update the Workload Certificate Feature Spec of a Membership.

  ## EXAMPLES

  To update the management of comma separated Memberships like
  `membership1,membership2`, run:

    $ {command} --memberships=MEMBERSHIP1,MEMBERSHIP2

  To update the management of all Memberships, run:

    $ {command} --all-memberships
  """

  feature_name = 'workloadcertificate'

  @staticmethod
  def Args(parser):

    parser.add_argument(
        '--memberships',
        type=str,
        help='Membership names to update, separated by commas if multiple are supplied.',
    )
    parser.add_argument(
        '--all-memberships',
        action='store_true',
        default=False,
        help='If supplied, update Workload Certificate Management for all memberships.',
    )
    parser.add_argument(
        '--enable',
        action='store_true',
        help='Enable Workload Certificate Management for the memberships.')
    parser.add_argument(
        '--disable',
        action='store_true',
        help='Disable Workload Certificate Management for the memberships.',
    )

  def Run(self, args):
    if args.enable and args.disable:
      raise exceptions.Error('--enable and --disable cannot both be set.')

    # If neither flag is set, disable workload certificate management for the
    # memberships.
    enable = args.enable

    all_memberships = base.ListMemberships()
    if not all_memberships:
      raise exceptions.Error('No memberships available in the fleet.')
    memberships = []

    if args.all_memberships:
      memberships = all_memberships
    elif args.memberships:
      memberships = args.memberships.split(',')

    if not memberships:  # The user didn't provide --memberships.
      if console_io.CanPrompt():
        index = console_io.PromptChoice(
            options=all_memberships,
            message='Please specify a membership:\n',
            cancel_option=True)
        memberships.append(all_memberships[index])
      else:
        raise calliope_exceptions.RequiredArgumentException(
            '--memberships',
            ('Cannot prompt a console for membership. Membership is required. '
             'Please specify `--memberships` to select at least one membership.'
            ))

    for membership in memberships:
      if membership not in all_memberships:
        raise exceptions.Error(
            'Membership {} does not exist in the fleet.'.format(membership))

    # All memberships in memberships are valid.
    f = self.GetFeature()
    membership_specs = {}
    for membership_str in memberships:
      membership = self.MembershipResourceName(membership_str)
      patch = self.messages.MembershipFeatureSpec()

      # Use current spec if it exists.
      for name, spec in self.hubclient.ToPyDict(f.membershipSpecs).items():
        if name == membership and spec:
          patch = spec
          break

      if not patch.workloadcertificate:
        patch.workloadcertificate = self.messages.MembershipSpec()

      if enable:
        patch.workloadcertificate.certificateManagement = self.messages.MembershipSpec.CertificateManagementValueValuesEnum.ENABLED
      else:
        patch.workloadcertificate.certificateManagement = self.messages.MembershipSpec.CertificateManagementValueValuesEnum.DISABLED

      membership_specs[membership] = patch

    f = self.messages.Feature(
        membershipSpecs=self.hubclient.ToMembershipSpecs(membership_specs))
    self.Update(['membershipSpecs'], f)
