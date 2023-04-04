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
"""Describe Policy Controller feature command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.fleet import client
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.container.fleet import resources
from googlecloudsdk.command_lib.container.fleet.features import base


@calliope_base.Hidden
@calliope_base.ReleaseTracks(
    calliope_base.ReleaseTrack.ALPHA, calliope_base.ReleaseTrack.BETA
)
class Describe(base.DescribeCommand):
  """Describe Policy Controller feature.

  ## EXAMPLES

  To describe the Policy Controller feature:

      $ {command}
  """

  feature_name = 'policycontroller'

  @classmethod
  def Args(cls, parser):
    resources.AddMembershipResourceArg(
        parser,
        plural=True,
        membership_help=(
            'The membership names for which to display Policy Controller '
            'feature information.'
        ),
    )

  def Run(self, args):
    feature = self.GetFeature()
    if args.memberships is not None:
      memberships_filter = args.memberships
      if feature.membershipSpecs:
        specs = client.HubClient.ToPyDict(feature.membershipSpecs)
        filtered_specs = {}
        for membership_name in specs:
          if membership_name in memberships_filter:
            filtered_specs[membership_name] = specs[membership_name]
        feature.membershipSpecs = client.HubClient.ToProtoMap(
            self.messages.Feature.MembershipSpecsValue, filtered_specs
        )

      if feature.membershipStates:
        states = client.HubClient.ToPyDict(feature.membershipStates)
        filtered_states = {}
        for membership_name in states:
          if membership_name in memberships_filter:
            filtered_states[membership_name] = states[membership_name]
        feature.membershipStates = client.HubClient.ToProtoMap(
            self.messages.Feature.MembershipStatesValue, filtered_states
        )

    return feature
