# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""The command to list all the members with Cloud Build installed."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as gbase
from googlecloudsdk.command_lib.container.hub.features import base


@gbase.Hidden
class List(base.FeatureCommand, gbase.ListCommand):
  """Lists all members with Cloud Build installed.

  ## EXAMPLES

  To list all members with Cloud Build installed, run:

    $ {command}
  """

  feature_name = 'cloudbuild'

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat("""
    table(
            NAME:label=NAME:sort=1
      )
    """)

  def Run(self, args):
    feature = self.GetFeature(v1alpha1=True)
    feature_spec_memberships = _parse_feature_spec_memberships(
        feature, self.v1alpha1_messages)

    cluster_list = []
    for membership in feature_spec_memberships:
      cluster_list.append({'NAME': membership})

    return cluster_list


def _parse_feature_spec_memberships(feature, messages):
  """Return feature spec for every registered member."""
  if feature.cloudbuildFeatureSpec is None or feature.cloudbuildFeatureSpec.membershipConfigs is None:
    feature_spec_membership_details = []
  else:
    feature_spec_membership_details = feature.cloudbuildFeatureSpec.membershipConfigs.additionalProperties

  status = {}
  for membership_detail in feature_spec_membership_details:
    if membership_detail.value != messages.CloudBuildMembershipConfig():
      status[membership_detail.key] = membership_detail.value

  return status
