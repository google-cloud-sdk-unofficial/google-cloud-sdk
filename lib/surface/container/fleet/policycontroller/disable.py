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
"""The command to disable Policy Controller Feature."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.container.fleet import resources
from googlecloudsdk.command_lib.container.fleet.features import base


@calliope_base.Hidden
class Disable(base.UpdateCommand):
  """Disable Policy Controller Feature.

  Uninstalls Policy Controller.

  ## EXAMPLES

  To uninstall Policy Controller, run:

    $ {command}
  """

  feature_name = 'policycontroller'

  @classmethod
  def Args(cls, parser):
    resources.AddMembershipResourceArg(
        parser,
        plural=True,
        membership_help=(
            'The membership names for which to uninstall Policy '
            'Controller, separated by commas if multiple are '
            'supplied. Ignored if --all-memberships is supplied; '
            'if neither is supplied, a prompt will appear with all '
            'available memberships.'))
    parser.add_argument(
        '--all-memberships',
        action='store_true',
        help='If supplied, uninstall Policy Controller for all memberships in the fleet.',
        default=False)

  def Run(self, args):
    membership_specs = {}
    poco_not_installed = self.messages.PolicyControllerHubConfig.InstallSpecValueValuesEnum(
        self.messages.PolicyControllerHubConfig.InstallSpecValueValuesEnum
        .INSTALL_SPEC_NOT_INSTALLED)

    poco_hub_config = self.messages.PolicyControllerHubConfig(
        installSpec=poco_not_installed)

    memberships = base.ParseMembershipsPlural(
        args, prompt=True, prompt_cancel=False, search=True)

    for membership in memberships:
      membership_path = membership
      membership_specs[membership_path] = self.messages.MembershipFeatureSpec(
          policycontroller=self.messages.PolicyControllerMembershipSpec(
              policyControllerHubConfig=poco_hub_config))

    patch = self.messages.Feature(
        membershipSpecs=self.hubclient.ToMembershipSpecs(membership_specs))
    return self.Update(['membership_specs'], patch)
