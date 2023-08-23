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

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.container.fleet.features import base
from googlecloudsdk.command_lib.container.fleet.policycontroller import flags
from googlecloudsdk.command_lib.container.fleet.policycontroller import utils
from googlecloudsdk.core import exceptions


@calliope_base.Hidden
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
    cmd_flags = flags.PocoFlags(parser, 'enable')

    # Scope Flags
    cmd_flags.add_memberships()

    # Configuration Flags
    cmd_flags.add_audit_interval()
    cmd_flags.add_constraint_violation_limit()
    cmd_flags.add_exemptable_namespaces()
    cmd_flags.add_log_denies_enabled()
    cmd_flags.add_monitoring()
    cmd_flags.add_mutation()
    cmd_flags.add_referential_rules()
    cmd_flags.add_template_library()
    cmd_flags.add_version()

  def Run(self, args):
    membership_specs = {}
    poco_hub_config = utils.set_poco_hub_config_parameters_from_args(
        args, self.messages
    )

    poco_hub_config.installSpec = self.messages.PolicyControllerHubConfig.InstallSpecValueValuesEnum(
        self.messages.PolicyControllerHubConfig.InstallSpecValueValuesEnum.INSTALL_SPEC_ENABLED
    )

    memberships = base.ParseMembershipsPlural(
        args, prompt=True, prompt_cancel=False, search=True
    )
    for membership in memberships:
      poco_membership_spec = self.messages.PolicyControllerMembershipSpec(
          policyControllerHubConfig=poco_hub_config
      )
      if args.version:
        poco_membership_spec.version = args.version

      membership_path = membership
      membership_specs[membership_path] = self.messages.MembershipFeatureSpec(
          policycontroller=poco_membership_spec
      )

    f = self.messages.Feature(
        membershipSpecs=self.hubclient.ToMembershipSpecs(membership_specs)
    )

    try:
      return self.Update(['membership_specs'], f)
    except exceptions.Error as e:
      fne = self.FeatureNotEnabledError()
      if str(e) == str(fne):
        return self.Enable(f)
      else:
        raise e
