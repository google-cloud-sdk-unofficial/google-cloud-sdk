# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Command for describing managed instance groups."""
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import managed_instance_groups_utils
from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Describe(base_classes.ZonalDescriber):
  """Describe a managed instance group."""

  @staticmethod
  def Args(parser):
    base_classes.ZonalDescriber.Args(parser)

  @property
  def service(self):
    return self.compute.instanceGroupManagers

  @property
  def resource_type(self):
    return 'instanceGroupManagers'

  def ComputeDynamicProperties(self, args, items):
    """Add Autoscaler information if Autoscaler is defined for the item."""
    # Items are expected to be IGMs.
    return managed_instance_groups_utils.AddAutoscalersToMigs(
        migs_iterator=items,
        project=self.project,
        compute=self.compute,
        http=self.http,
        batch_url=self.batch_url,
        fail_when_api_not_supported=False)


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class DescribeBeta(base_classes.MultiScopeDescriber):
  """Describe a managed instance group."""

  SCOPES = [base_classes.ScopeType.regional_scope,
            base_classes.ScopeType.zonal_scope]

  @property
  def global_service(self):
    return None

  @property
  def regional_service(self):
    return self.compute.regionInstanceGroupManagers

  @property
  def zonal_service(self):
    return self.compute.instanceGroupManagers

  @property
  def global_resource_type(self):
    return None

  @property
  def regional_resource_type(self):
    return 'regionInstanceGroupManagers'

  @property
  def zonal_resource_type(self):
    return 'instanceGroupManagers'

  @staticmethod
  def Args(parser):
    base_classes.MultiScopeDescriber.AddScopeArgs(
        parser, 'instanceGroupManagers', DescribeBeta.SCOPES)

  def ComputeDynamicProperties(self, args, items):
    """Add Autoscaler information if Autoscaler is defined for the item."""
    # Items are expected to be IGMs.
    return managed_instance_groups_utils.AddAutoscalersToMigs(
        migs_iterator=items,
        project=self.project,
        compute=self.compute,
        http=self.http,
        batch_url=self.batch_url,
        fail_when_api_not_supported=False)


Describe.detailed_help = {
    'brief': 'Describe a managed instance group',
    'DESCRIPTION': """\
        *{command}* displays all data associated with a Google Compute Engine
managed instance group.
""",
}
DescribeBeta.detailed_help = base_classes.GetMultiScopeDescriberHelp(
    'managed instance group', DescribeBeta.SCOPES)
