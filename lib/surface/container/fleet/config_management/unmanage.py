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
"""The command to unmanage/delete Config Management Feature."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.container.fleet.features import base
from googlecloudsdk.core import exceptions
from googlecloudsdk.core.console import console_io


class Unmanage(base.UpdateCommand):
  """Remove the Config Management Feature Spec for the given membership.

  Remove the Config Management Feature Spec for the given membership. The
  existing ConfigManagement resources in the clusters will become unmanaged.

  ## EXAMPLES

  To remove the Config Management Feature spec for a membership, run:

    $ {command} --membership=MEMBERSHIP_NAME
  """

  feature_name = 'configmanagement'

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        '--membership',
        type=str,
        help='The Membership name provided during registration.',
    )

  def Run(self, args):
    memberships = base.ListMemberships()
    if not memberships:
      raise exceptions.Error('No Memberships available in the fleet.')
    # User should choose an existing membership if not provide one
    if not args.membership:
      index = console_io.PromptChoice(
          options=memberships,
          message='Please specify a membership to '
          'unmanage in configmanagement:\n')
      membership = memberships[index]
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
