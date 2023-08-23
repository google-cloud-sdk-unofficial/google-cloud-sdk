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

from apitools.base.protorpclite import messages
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.container.fleet.features import base
from googlecloudsdk.command_lib.container.fleet.policycontroller import command
from googlecloudsdk.command_lib.container.fleet.policycontroller import flags


@calliope_base.Hidden
class Update(base.UpdateCommand, command.PocoCommand):
  """Updates the configuration of Policy Controller Feature.

  Updates the configuration of the Policy Controller installation
  ## EXAMPLES

  To change the installed version, run:

    $ {command} --version=VERSION

  To modify the audit interval to 120 seconds, run:

    $ {command} --audit-interval=120
  """

  feature_name = 'policycontroller'

  @classmethod
  def Args(cls, parser):
    cmd_flags = flags.PocoFlags(parser, 'update')

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
    parser = flags.PocoFlagParser(args, self.messages)
    specs = self.path_specs(args)
    updated_specs = {path: self.update(s, parser) for path, s in specs.items()}
    return self.update_specs(updated_specs)

  def update(self, spec: messages.Message, parser: flags.PocoFlagParser):
    pc = spec.policycontroller
    pc = parser.update_version(pc)

    hub_cfg = pc.policyControllerHubConfig
    hub_cfg = parser.update_audit_interval(hub_cfg)
    hub_cfg = parser.update_constraint_violation_limit(hub_cfg)
    hub_cfg = parser.update_exemptable_namespaces(hub_cfg)
    hub_cfg = parser.update_log_denies(hub_cfg)
    hub_cfg = parser.update_mutation(hub_cfg)
    hub_cfg = parser.update_monitoring(hub_cfg)
    hub_cfg = parser.update_referential_rules(hub_cfg)
    hub_cfg = parser.update_template_library(hub_cfg)

    pc.policyControllerHubConfig = hub_cfg
    spec.policycontroller = pc
    return spec
