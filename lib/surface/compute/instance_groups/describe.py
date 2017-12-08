# Copyright 2014 Google Inc. All Rights Reserved.
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
"""Command for describing instance groups."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import instance_groups_utils


class Describe(base_classes.MultiScopeDescriber):
  """Describe an instance group."""

  SCOPES = (base_classes.ScopeType.regional_scope,
            base_classes.ScopeType.zonal_scope)

  @property
  def global_service(self):
    return None

  @property
  def regional_service(self):
    return self.compute.regionInstanceGroups

  @property
  def zonal_service(self):
    return self.compute.instanceGroups

  @property
  def global_resource_type(self):
    return None

  @property
  def regional_resource_type(self):
    return 'regionInstanceGroups'

  @property
  def zonal_resource_type(self):
    return 'instanceGroups'

  @staticmethod
  def Args(parser):
    base_classes.MultiScopeDescriber.AddScopeArgs(
        parser, 'instanceGroups', Describe.SCOPES)

  def ComputeDynamicProperties(self, args, items):
    return instance_groups_utils.ComputeInstanceGroupManagerMembership(
        compute=self.compute,
        project=self.project,
        http=self.http,
        batch_url=self.batch_url,
        items=items,
        filter_mode=instance_groups_utils.InstanceGroupFilteringMode.ALL_GROUPS)


Describe.detailed_help = base_classes.GetMultiScopeDescriberHelp(
    'instance group', Describe.SCOPES)
