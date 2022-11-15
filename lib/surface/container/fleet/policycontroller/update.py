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
"""The command to update Policy Controller Feature."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.container.fleet import resources
from googlecloudsdk.command_lib.container.fleet.features import base
from googlecloudsdk.command_lib.container.fleet.policycontroller import utils
from googlecloudsdk.core import exceptions


class Update(base.UpdateCommand):
  """Updates the configuration of Policy Controller Feature.

  Updates the configuration of the Policy Controller installation
  ## EXAMPLES

  To change the installed version, run:

    $ {command} --version=VERSION

  To modify the audit interval to 120 seconds, run:

    $ {command} --audit-interval-seconds=120
  """
  feature_name = 'policycontroller'

  @classmethod
  def Args(cls, parser):
    resources.AddMembershipResourceArg(
        parser,
        plural=True,
        membership_help=(
            'The membership names to update, separated by commas if multiple '
            'are supplied. Ignored if --all-memberships is supplied; if '
            'neither is supplied, a prompt will appear with all available '
            'memberships.'))
    parser.add_argument(
        '--all-memberships',
        action='store_true',
        help='If supplied, update Policy Controller for all memberships in the fleet.',
        default=False,
    )
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
        '--no-exemptable-namespaces',
        action='store_true',
        help='Disables any namespace exemptions, enabling Policy Controller on all namespaces.'
    )
    parser.add_argument(
        '--log-denies-enabled',
        action=utils.BooleanOptionalAction,
        const=None,
        help='If set, log all denies and dry run failures. (To disable, use --no-log-denies-enabled)'
    )
    parser.add_argument(
        '--mutation-enabled',
        action=utils.BooleanOptionalAction,
        help='If set, enable support for mutation. (To disable, use --no-mutation-enabled)'
    )
    parser.add_argument(
        '--referential-rules-enabled',
        action=utils.BooleanOptionalAction,
        help='If set, enable support for referential constraints. (To disable, use --no-referential-rules-enabled)'
    )
    parser.add_argument(
        '--template-library-installed',
        action=utils.BooleanOptionalAction,
        help='If set, install a library of constraint templates for common policy types. (To disable, use --no-template-library-installed)'
    )
    parser.add_argument(
        '--monitoring',
        type=str,
        help='Monitoring backend options Policy Controller should export metrics to, separated by commas if multiple are supplied. Options: prometheus, cloudmonitoring'
    )
    parser.add_argument(
        '--no-monitoring',
        action='store_true',
        help='Include this flag to disable the monitoring configuration of Policy Controller'
    )
    parser.add_argument(
        '--version',
        type=str,
        help='The version of Policy Controller to install.')
    parser.add_argument(
        '--suspend',
        action=utils.BooleanOptionalAction,
        help='If set, suspend Policy Controller webhooks and only preserve the audit functionality. (To resume normal operation, use --no-suspend)'
    )

  def Run(self, args):
    membership_specs = self.hubclient.ToPyDict(
        self.GetFeature().membershipSpecs)
    poco_hub_config = utils.set_poco_hub_config_parameters_from_args(
        args, self.messages)
    memberships = base.ParseMembershipsPlural(
        args, search=True, prompt=True, prompt_cancel=False, autoselect=True)
    for membership in memberships:
      full_membership_name = ''
      full_membership_name = utils.convert_membership_from_project_id_to_number(
          membership)
      if full_membership_name not in membership_specs:
        raise exceptions.Error(
            'Policy Controller is not enabled for membership {}'.format(
                membership))
      current_poco_membership_spec = membership_specs[
          full_membership_name].policycontroller
      poco_hub_config = current_poco_membership_spec.policyControllerHubConfig
      current_version = current_poco_membership_spec.version
      utils.merge_args_with_poco_hub_config(args, poco_hub_config,
                                            self.messages)
      poco_membership_spec = self.messages.PolicyControllerMembershipSpec(
          policyControllerHubConfig=poco_hub_config, version=current_version)
      if args.version:
        poco_membership_spec.version = args.version

      membership_specs[
          full_membership_name] = self.messages.MembershipFeatureSpec(
              policycontroller=poco_membership_spec)

    patch = self.messages.Feature(
        membershipSpecs=self.hubclient.ToMembershipSpecs(membership_specs))
    return self.Update(['membership_specs'], patch)
