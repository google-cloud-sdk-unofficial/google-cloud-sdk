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

from googlecloudsdk.api_lib.container.fleet import util as fleet_util
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.container.fleet.features import base
from googlecloudsdk.command_lib.container.fleet.policycontroller import flags
from googlecloudsdk.command_lib.container.fleet.policycontroller import utils
from googlecloudsdk.core import exceptions


@calliope_base.Hidden
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
    cmd_flags = flags.Flags(parser, 'update')

    # Scope Flags
    cmd_flags.AddMemberships()

    # Configuration Flags
    cmd_flags.AddAuditInterval()
    cmd_flags.AddConstraintViolationLimit()
    cmd_flags.AddExemptableNamespaces()
    cmd_flags.AddLogDeniesEnabled()
    cmd_flags.AddMonitoring()
    cmd_flags.AddMutationEnabled()
    cmd_flags.AddReferentialRulesEnabled()
    cmd_flags.AddTemplateLibraryInstall()
    cmd_flags.AddVersion()

  def Run(self, args):
    membership_specs = self.hubclient.ToPyDict(
        self.GetFeature().membershipSpecs
    )
    memberships = base.ParseMembershipsPlural(
        args, search=True, prompt=True, prompt_cancel=False, autoselect=True
    )
    memberships_short_path = [
        fleet_util.MembershipPartialName(membership)
        for membership in memberships
    ]
    membership_specs_short_path = {
        fleet_util.MembershipPartialName(full_path): ms
        for full_path, ms in membership_specs.items()
        if fleet_util.MembershipPartialName(full_path) in memberships_short_path
    }

    # Remove spec entries that are not specified in this command.
    for membership in list(membership_specs.keys()):
      shortname = fleet_util.MembershipPartialName(membership)
      if shortname not in memberships_short_path:
        del membership_specs[membership]

    for membership in memberships:
      short_membership = fleet_util.MembershipPartialName(membership)
      if short_membership not in membership_specs_short_path:
        raise exceptions.Error(
            'Policy Controller is not enabled for membership {}'.format(
                membership
            )
        )
      # make changes to membership spec in place, so that we don't have to deal
      # with project ID/number conversion.
      current_poco_membership_spec = membership_specs_short_path[
          short_membership
      ].policycontroller
      poco_hub_config = current_poco_membership_spec.policyControllerHubConfig
      utils.merge_args_with_poco_hub_config(
          args, poco_hub_config, self.messages
      )
      if args.version:
        current_poco_membership_spec.version = args.version

    patch = self.messages.Feature(
        membershipSpecs=self.hubclient.ToMembershipSpecs(membership_specs)
    )
    return self.Update(['membership_specs'], patch)
