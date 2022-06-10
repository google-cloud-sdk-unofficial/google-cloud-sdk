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

import sys
from googlecloudsdk.command_lib.container.fleet.features import base
from googlecloudsdk.core import exceptions
from googlecloudsdk.core.console import console_io


class Delete(base.UpdateCommand):
  """Remove the Identity Service Feature Spec for the given membership.

  Removes the Identity Service Feature Spec for the given
  membership.

  ## EXAMPLES

  To delete an Identity Service configuration for a membership, run:

    $ {command} --membership=MEMBERSHIP_NAME
  """

  feature_name = 'identityservice'

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--membership',
        type=str,
        help=('Membership name provided during registration.'),
    )

  def Run(self, args):
    # Get fleet memberships (cluster registered with fleet) from GCP Project.
    memberships = base.ListMemberships()
    if not memberships:
      raise exceptions.Error('No Memberships available in the fleet.')

    # Acquire membership.
    membership = None
    # Prompt user for an existing fleet membership if none is provided.
    if not args.membership:
      index = 0
      if len(memberships) > 1:
        index = console_io.PromptChoice(
            options=memberships,
            message='Please specify a membership to delete Identity Service {}:\n'
        )
      membership = memberships[index]
      sys.stderr.write('Selecting membership [{}].\n'.format(membership))
    else:
      membership = args.membership
      if membership not in memberships:
        raise exceptions.Error(
            'Membership {} is not in the fleet.'.format(membership))

    # Setup a patch to set the MembershipSpec to the empty proto ("delete").
    membership_key = self.MembershipResourceName(membership)
    specs = {membership_key: self.messages.MembershipFeatureSpec()}
    patch = self.messages.Feature(
        membershipSpecs=self.hubclient.ToMembershipSpecs(specs))

    self.Update(['membership_specs'], patch)
