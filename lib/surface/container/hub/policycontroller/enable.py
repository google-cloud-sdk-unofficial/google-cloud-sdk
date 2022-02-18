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

from googlecloudsdk.command_lib.container.hub.features import base
from googlecloudsdk.core import exceptions
from googlecloudsdk.core.console import console_io


class Enable(base.EnableCommand):
  """Enable Policy Controller Feature.

  Enables the Policy Controller Feature in Hub.

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
        help='If supplied, enable Policy Controller for all memberships in the Hub.',
        default=False)
    parser.add_argument(
        '--template-library-installed',
        action='store_true',
        help='Install template libraries.',
        default=False)
    parser.add_argument(
        '--version',
        type=str,
        help='The version of Policy Controller to install; defaults to latest version.'
    )
    parser.add_argument(
        '--referential-rules-enabled',
        action='store_true',
        help='Enable support for referential constraints.',
        default=False)
    parser.add_argument(
        '--audit-interval-seconds',
        type=int,
        help='How often Policy Controller will audit resources, in seconds.',
        default=60)
    parser.add_argument(
        '--log-denies-enabled',
        action='store_true',
        help='Log all denies and dry run failures.',
        default=False)
    parser.add_argument(
        '--exemptable-namespaces',
        type=str,
        help='Namespaces that Policy Controller should ignore, separated by commas if multiple are supplied.'
    )

  def Run(self, args):
    membership_specs = {}
    pc_membership_config = self.messages.PolicyControllerPolicyControllerHubConfig(
    )

    memberships = []
    all_memberships = base.ListMemberships()

    if args.all_memberships:
      memberships = all_memberships
    elif args.memberships:
      memberships = args.memberships.split(',')
      for membership in memberships:
        if membership not in all_memberships:
          raise exceptions.Error('Membership {} not found'.format(membership))
    else:
      index = console_io.PromptChoice(
          options=all_memberships, message='Please specify a membership:\n')
      memberships = [all_memberships[index]]

    if not memberships:
      raise exceptions.Error('A membership is required before enabling.')

    if args.referential_rules_enabled:
      pc_membership_config.referentialRulesEnabled = True
    if args.template_library_installed:
      pc_membership_config.templateLibraryConfig = self.messages.PolicyControllerTemplateLibraryConfig(
          included=True)
    if args.version:
      pc_membership_config.version = args.version
    if args.audit_interval_seconds:
      pc_membership_config.auditIntervalSeconds = args.audit_interval_seconds
    if args.log_denies_enabled:
      pc_membership_config.logDeniesEnabled = True
    if args.exemptable_namespaces:
      exemptable_namespaces = args.exemptable_namespaces.split(',')
      pc_membership_config.exemptableNamespaces = exemptable_namespaces

    for membership in memberships:
      membership_specs[self.MembershipResourceName(
          membership)] = self.messages.MembershipFeatureSpec(
              policycontroller=self.messages.PolicyControllerMembershipSpec(
                  policyControllerHubConfig=pc_membership_config))

    f = self.messages.Feature(
        membershipSpecs=self.hubclient.ToMembershipSpecs(membership_specs))

    return self.Enable(f)
