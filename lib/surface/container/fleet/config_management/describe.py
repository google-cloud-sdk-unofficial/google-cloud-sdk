# -*- coding: utf-8 -*- #
# Copyright 2025 Google LLC. All Rights Reserved.
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
"""The command to view the Config Management Feature."""

from googlecloudsdk.api_lib.util import exceptions as gcloud_exception
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.fleet import resources
from googlecloudsdk.command_lib.container.fleet.config_management import utils
from googlecloudsdk.command_lib.container.fleet.features import base as features_base


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Describe(features_base.DescribeCommand):
  """Describe the Config Management feature."""
  feature_name = utils.CONFIG_MANAGEMENT_FEATURE_NAME


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class DescribeAlpha(Describe):
  """Describe the Config Management feature.

  ## EXAMPLES

  To describe the entire Config Management feature, run:

    $ {command}

  To describe select membership configurations, run:

    $ {command} --memberships=example-membership-1,example-membership-2
  """

  @staticmethod
  def Args(parser):
    # Create group to add help text.
    memberships_group = parser.add_group(
        help=(
            'Memberships to print configurations for.'
            ' Errors if a specified membership does not have a configuration'
            ' for this feature.'
        )
    )
    resources.AddMembershipResourceArg(memberships_group, plural=True)

  @gcloud_exception.CatchHTTPErrorRaiseHTTPException('{message}')
  def Run(self, args):
    feature = self.GetFeature()
    if args.memberships:
      # Verify the specified Memberships exist to distinguish them from
      # Memberships that have no specs in error messages.
      memberships = features_base.ParseMembershipsPlural(args, search=True)
      self.filter_feature_for_memberships(feature, memberships)
    return feature
