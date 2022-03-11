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
"""The command to get the version of all memberships with the Config Management Feature enabled."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.fleet import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.fleet.features import base as feature_base

NA = 'NA'


class ConfigmanagementFeatureState(object):
  """Feature state class stores ACM status."""

  def __init__(self, clusterName):
    self.name = clusterName
    self.version = NA


class Version(feature_base.FeatureCommand, base.ListCommand):
  """Print the version of all clusters with Config Management enabled.

  ## EXAMPLES

  To print the version of all clusters with Config Management enabled, run:

    $ {command}
  """

  feature_name = 'configmanagement'

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat(
        'table(name:label=Name:sort=1,version:label=Version)')

  def Run(self, args):
    memberships = feature_base.ListMemberships()
    f = self.GetFeature()

    acm_status = []
    feature_state_memberships = feature_state_memberships = {
        util.MembershipShortname(m): s
        for m, s in self.hubclient.ToPyDict(f.membershipStates).items()
    }
    for name in memberships:
      cluster = ConfigmanagementFeatureState(name)
      if name not in feature_state_memberships:
        acm_status.append(cluster)
        continue
      md = feature_state_memberships[name]
      fs = md.configmanagement
      if fs and fs.membershipSpec and fs.membershipSpec.version:
        cluster.version = fs.membershipSpec.version
      acm_status.append(cluster)

    return acm_status
