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
"""The command to update a Cloud Build cluster."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as gbase
from googlecloudsdk.command_lib.container.hub.build import utils
from googlecloudsdk.command_lib.container.hub.features import base
from googlecloudsdk.core import exceptions
from googlecloudsdk.core.console import console_io


@gbase.Hidden
class Update(base.UpdateCommand):
  """Update the Cloud Build configuration on the specified member.

  ## EXAMPLES

  To update the security policy configuration on a membership named
  [MEMBERSHIP-ID], run:

    $ {command} --membership=[MEMBERSHIP-ID]
    --security-policy=[SECURITYPOLICY]

  """

  feature_name = 'cloudbuild'

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        '--membership',
        type=str,
        help='The name of the Membership to update.',
        required=True,
    )
    parser.add_argument(
        '--security-policy',
        type=str,
        default='NON_PRIVILEGED',
        choices=['NON_PRIVILEGED', 'PRIVILEGED'],
        help='Privilege options for build steps.',
        required=True,
    )

  def Run(self, args):
    feature = self.GetFeature(v1alpha1=True)
    membership = args.membership
    utils.VerifyMembership(membership)

    feature_spec_memberships = utils.GetFeatureSpecMemberships(
        feature, self.v1alpha1_messages)
    if membership not in feature_spec_memberships:
      raise exceptions.Error(
          'No Cloud Build hybrid worker pool installation was registered for this membership.'
      )

    spec = feature_spec_memberships[membership]
    securitypolicy = utils.ParseSecuritypolicy(args.security_policy,
                                               self.v1alpha1_messages)
    warn_securitypolicy_update(self.v1alpha1_messages, securitypolicy,
                               spec.securityPolicy, membership)
    spec.securityPolicy = securitypolicy
    f = utils.MembershipSpecPatch(self.v1alpha1_messages, membership, spec)
    self.Update(['cloudbuild_feature_spec.membership_configs'],
                f,
                v1alpha1=True)


def warn_securitypolicy_update(messages, securitypolicy_requested,
                               securitypolicy_installed, membership):
  if securitypolicy_installed == messages.CloudBuildMembershipConfig.SecurityPolicyValueValuesEnum.PRIVILEGED and securitypolicy_requested == messages.CloudBuildMembershipConfig.SecurityPolicyValueValuesEnum.NON_PRIVILEGED:
    console_io.PromptContinue(
        '\nYou are attempting to change the security policy from PRIVILEGED to NON_PRIVILEGED for member {}.\n'
        'Please note that while you can change the configuration to NON_PRIVILEGED,this member may have been tainted while it was in PRIVILEGED mode.'
        .format(membership),
        'Do you want to continue?',
        throw_if_unattended=True,
        cancel_on_no=True)
