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
"""The command to enable Policy Controller Feature."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.container.fleet.features import base
from googlecloudsdk.command_lib.container.fleet.policycontroller import utils
from googlecloudsdk.core import exceptions


class Enable(base.UpdateCommand, base.EnableCommand):
  """Enable Policy Controller Feature.

  Enables the Policy Controller Feature in a fleet.

  ## EXAMPLES

  To enable the Policy Controller Feature, run:

    $ {command}
  """

  feature_name = 'policycontroller'

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        '--memberships',
        type=str,
        help='The membership names to update, separated by commas if multiple are supplied. Ignored if --all-memberships is supplied; if neither is supplied, a prompt will appear with all available memberships.',
    )
    parser.add_argument(
        '--all-memberships',
        action='store_true',
        help='If supplied, enable Policy Controller for all memberships in the fleet.',
        default=False)
    parser.add_argument(
        '--audit-interval-seconds',
        type=int,
        help='How often Policy Controller will audit resources, in seconds.',
        default=60)
    parser.add_argument(
        '--exemptable-namespaces',
        type=str,
        help='Namespaces that Policy Controller should ignore, separated by commas if multiple are supplied.'
    )
    parser.add_argument(
        '--log-denies-enabled',
        action='store_true',
        help='Log all denies and dry run failures.',
        default=False)
    parser.add_argument(
        '--referential-rules-enabled',
        action='store_true',
        help='Enable support for referential constraints.',
        default=False)
    parser.add_argument(
        '--template-library-installed',
        action='store_true',
        help='Install a library of constraint templates for common policy types.',
        default=False)
    parser.add_argument(
        '--version',
        type=str,
        help='The version of Policy Controller to install; defaults to latest version.'
    )

  def Run(self, args):
    membership_specs = {}
    poco_hub_config = utils.set_poco_hub_config_parameters_from_args(
        args, self.messages)
    poco_hub_config.installSpec = self.messages.PolicyControllerHubConfig.InstallSpecValueValuesEnum(
        self.messages.PolicyControllerHubConfig
        .InstallSpecValueValuesEnum.INSTALL_SPEC_ENABLED)

    memberships = utils.select_memberships(args)
    for membership in memberships:
      poco_membership_spec = self.messages.PolicyControllerMembershipSpec(
          policyControllerHubConfig=poco_hub_config)
      if args.version:
        poco_membership_spec.version = args.version

      membership_specs[self.MembershipResourceName(
          membership)] = self.messages.MembershipFeatureSpec(
              policycontroller=poco_membership_spec)

    f = self.messages.Feature(
        membershipSpecs=self.hubclient.ToMembershipSpecs(membership_specs))

    try:
      return self.Update(['membership_specs'], f)
    except exceptions.Error as e:
      fne = self.FeatureNotEnabledError()
      if str(e) == str(fne):
        return self.Enable(f)
      else:
        raise e
