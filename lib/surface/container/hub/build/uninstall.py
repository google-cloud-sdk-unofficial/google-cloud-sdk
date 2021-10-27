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
"""The command to uninstall Cloud Build from a cluster."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as gbase
from googlecloudsdk.command_lib.container.hub.build import utils
from googlecloudsdk.command_lib.container.hub.features import base
from googlecloudsdk.core import log


@gbase.Hidden
class Uninstall(base.UpdateCommand):
  """Uninstall Cloud Build from the specified member.

  ## EXAMPLES

  To uninstall Cloud Build from a membership named MEMBERSHIP-ID, run:

    $ {command} --membership=[MEMBERSHIP-ID]
  """

  feature_name = 'cloudbuild'

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        '--membership',
        type=str,
        help='The name of the Membership to uninstall Cloud Build from.',
        required=True,
    )

  def Run(self, args):
    feature = self.GetFeature(v1alpha1=True)
    membership = args.membership
    utils.VerifyMembership(membership)

    feature_spec_memberships = utils.GetFeatureSpecMemberships(
        feature, self.v1alpha1_messages)
    if membership not in feature_spec_memberships:
      log.warning(
          'No Cloud Build installation was registered for this membership.')

    spec = self.v1alpha1_messages.CloudBuildMembershipConfig()
    f = utils.MembershipSpecPatch(self.v1alpha1_messages, membership, spec)
    self.Update(['cloudbuild_feature_spec.membership_configs'],
                f,
                v1alpha1=True)
