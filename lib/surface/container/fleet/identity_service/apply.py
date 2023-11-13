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
"""The command to update Identity Service Feature."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.anthos.common import file_parsers
from googlecloudsdk.command_lib.container.fleet import resources
from googlecloudsdk.command_lib.container.fleet.features import base
from googlecloudsdk.command_lib.container.fleet.identity_service import utils


# Pull out the example text so the example command can be one line without the
# py linter complaining. The docgen tool properly breaks it into multiple lines.
EXAMPLES = """\
    To apply an Identity Service configuration to a membership, run:

    $ {command} --membership=MEMBERSHIP_NAME --config=/path/to/identity-service.yaml
"""


class Apply(base.UpdateCommand):
  """Update an Identity Service Feature Spec.

  Applies the authentication configuration to the Identity Service feature spec
  for this membership. This configuration is now the "source of truth" for the
  cluster and can only be updated by using this command or the Cloud Console.
  Any local authentication configuration on the cluster is overwritten by this
  configuration, including any local updates made after you run this command.
  """

  detailed_help = {'EXAMPLES': EXAMPLES}

  feature_name = 'identityservice'

  @classmethod
  def Args(cls, parser):
    command_args = parser.add_group(required=True, mutex=False)
    command_args.add_argument(
        '--fleet-default-member-config',
        type=str,
        help='The path to an identity-service.yaml config file.',
        hidden=True,
        required=False,
    )

    per_member_config_args = command_args.add_group(required=False, mutex=False)
    resources.AddMembershipResourceArg(per_member_config_args)
    per_member_config_args.add_argument(
        '--config',
        type=str,
        help='The path to an identity-service.yaml config file.',
        required=True,
    )

  def Run(self, args):
    patch = self.messages.Feature()
    update_mask = []
    if args.config:
      self.preparePerMemberConfigPatch(args, patch, update_mask)

    if args.fleet_default_member_config:
      self.prepareFleetDefaultMemberConfigPatch(args, patch, update_mask)

    self.Update(update_mask, patch)

  def prepareFleetDefaultMemberConfigPatch(self, args, patch, update_mask):
    # Load the config YAML file.
    loaded_config = file_parsers.YamlConfigFile(
        file_path=args.fleet_default_member_config,
        item_type=file_parsers.LoginConfigObject,
    )

    # Create a new identity service feature spec.
    member_config = utils.parse_config(loaded_config, self.messages)

    # Add the fleet default member config to the feature patch and update
    # `update mask`.
    patch.fleetDefaultMemberConfig = (
        self.messages.CommonFleetDefaultMemberConfigSpec(
            identityservice=member_config
        )
    )
    update_mask.append('fleet_default_member_config')

  def preparePerMemberConfigPatch(self, args, patch, update_mask):
    # Get the membership the user is attempting to apply the configuration to.
    # This will prompt the user to select a membership from the ones available
    # in the fleet if none is provided.
    membership = base.ParseMembership(
        args, prompt=True, autoselect=True, search=True
    )

    # Load the config YAML file.
    loaded_config = file_parsers.YamlConfigFile(
        file_path=args.config, item_type=file_parsers.LoginConfigObject
    )

    # Create a new identity service feature spec.
    member_config = utils.parse_config(loaded_config, self.messages)

    # UpdateFeature uses the patch method to update the member_configs map, so
    # there's no need to fetch the existing feature spec.
    specs = {
        membership: self.messages.MembershipFeatureSpec(
            identityservice=member_config
        )
    }

    # Add the newly prepared membership specs to the feature patch and update
    # `update mask`.
    patch.membershipSpecs = self.hubclient.ToMembershipSpecs(specs)
    update_mask.append('membership_specs')
