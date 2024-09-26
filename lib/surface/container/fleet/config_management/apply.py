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
"""The command to update Config Management Feature."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.fleet import resources
from googlecloudsdk.command_lib.container.fleet.config_management import command
from googlecloudsdk.command_lib.container.fleet.config_management import utils
from googlecloudsdk.command_lib.container.fleet.features import base as fleet_base
from googlecloudsdk.command_lib.container.fleet.membershipfeatures import base as mf_base
from googlecloudsdk.command_lib.container.fleet.membershipfeatures import convert
from googlecloudsdk.command_lib.container.fleet.membershipfeatures import util as mf_util

# Pull out the example text so the example command can be one line without the
# py linter complaining. The docgen tool properly breaks it into multiple lines.
EXAMPLES = r"""
    To apply a YAML config file to a membership, prepare
    [apply-spec.yaml](https://cloud.google.com/anthos-config-management/docs/reference/gcloud-apply-fields#example_gcloud_apply_spec) then run:

      $ {command} --membership=MEMBERSHIP_NAME --config=APPLY-SPEC.YAML --version=VERSION
"""


@base.DefaultUniverseOnly
class Apply(fleet_base.UpdateCommand, mf_base.UpdateCommand, command.Common):
  """Update a Config Management Feature Spec.

  Update a user-specified config file to a ConfigManagement Custom Resource.
  The config file should be a .yaml file, all eligible fields are listed in
  https://cloud.google.com/anthos-config-management/docs/reference/gcloud-apply-fields
  """

  detailed_help = {'EXAMPLES': EXAMPLES}

  feature_name = utils.CONFIG_MANAGEMENT_FEATURE_NAME
  mf_name = utils.CONFIG_MANAGEMENT_FEATURE_NAME

  @classmethod
  def Args(cls, parser):
    resources.AddMembershipResourceArg(parser)
    parser.add_argument(
        '--config',
        type=str,
        help='The path to config-management.yaml.',
        required=True,
    )
    parser.add_argument(
        '--version', type=str, help='The version of ACM to install.'
    )

  def Run(self, args):
    utils.enable_poco_api_if_disabled(self.Project())

    # check static yaml fields before query membership
    cm = self.parse_config_management(args.config)
    cm.version = args.version
    membership = fleet_base.ParseMembership(
        args, prompt=True, autoselect=True, search=True
    )
    if (not cm.version and
        cm.management !=
        self.messages.ConfigManagementMembershipSpec.ManagementValueValuesEnum.MANAGEMENT_AUTOMATIC):
      cm.version = self._get_backfill_version(membership)

    # UpdateFeature uses patch method to update membership_configs map,
    # there's no need to get the existing feature spec
    patch = self.messages.Feature(
        membershipSpecs=self.hubclient.ToMembershipSpecs({
            membership: self.messages.MembershipFeatureSpec(
                configmanagement=cm
            )
        })
    )

    use_fleet_default_config = (
        hasattr(args, 'origin')
        and args.origin is not None
    )
    if not use_fleet_default_config and mf_util.UseMembershipFeatureV2(
        self.ReleaseTrack()
    ):
      membershipfeature = convert.ToV2MembershipFeature(
          self, membership, self.mf_name,
          self.messages.MembershipFeatureSpec(configmanagement=cm),
      )
      self.UpdateV2(membership, ['spec'], membershipfeature)
    else:
      self.Update(['membership_specs'], patch)

  def _get_backfill_version(self, membership):
    """Get the value the version field in FeatureSpec should be set to.

    Args:
      membership: The full membership  name whose Spec will be backfilled.

    Returns:
      version: A string denoting the version field in MembershipConfig
    Raises: Error, if retrieving FeatureSpec of FeatureState fails
    """
    f = self.GetFeature()
    return utils.get_backfill_version_from_feature(f, membership)
