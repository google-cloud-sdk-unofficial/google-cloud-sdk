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
"""Command for listing managed instance groups."""
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import managed_instance_groups_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log


def _AutoscalerWithErrorInList(resources):
  """Checks, if there exists autoscaler, which reports errors."""
  for resource in resources:
    if resource['autoscaled'] == 'yes (*)':
      return True
  return False


class ListDynamicPropertisMixin(object):
  """Untilies for computling Autoscaler related data for 'list' commands."""

  def ComputeDynamicProperties(self, args, items):
    """Add Autoscaler information if Autoscaler is defined for the item."""
    _ = args
    # Items are expected to be IGMs.
    items = list(items)
    for mig in managed_instance_groups_utils.AddAutoscalersToMigs(
        migs_iterator=self.ComputeInstanceGroupSize(items=items),
        project=self.project,
        compute=self.compute,
        http=self.http,
        batch_url=self.batch_url,
        fail_when_api_not_supported=False):
      if 'autoscaler' in mig and mig['autoscaler'] is not None:
        if (hasattr(mig['autoscaler'], 'status') and mig['autoscaler'].status ==
            self.messages.Autoscaler.StatusValueValuesEnum.ERROR):
          mig['autoscaled'] = 'yes (*)'
        else:
          mig['autoscaled'] = 'yes'
      else:
        mig['autoscaled'] = 'no'
      yield mig


# TODO(user): This acts like
# instance-groups list --only-managed
# so they should share code.
@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA)
class List(ListDynamicPropertisMixin,
           base_classes.InstanceGroupManagerDynamicProperiesMixin,
           base_classes.ZonalLister):
  """List Google Compute Engine managed instance groups."""

  @property
  def service(self):
    return self.compute.instanceGroupManagers

  @property
  def resource_type(self):
    return 'instanceGroupManagers'

  def GetResources(self, args, errors):
    resources = super(List, self).GetResources(args, errors)
    return (resource for resource in resources if resource.zone)

  def Display(self, args, resources):
    """Prints the given resources."""
    resources = list(resources)
    super(List, self).Display(args, resources)
    if _AutoscalerWithErrorInList(resources):
      log.err.Print('(*) - there are errors in your autoscaling setup, please '
                    'describe the resource to see details')


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ListAlpha(ListDynamicPropertisMixin,
                base_classes.InstanceGroupManagerDynamicProperiesMixin,
                base_classes.MultiScopeLister):
  """List Google Compute Engine managed instance groups."""

  SCOPES = [base_classes.ScopeType.regional_scope,
            base_classes.ScopeType.zonal_scope]

  @staticmethod
  def Args(parser):
    base_classes.MultiScopeLister.AddScopeArgs(parser, ListAlpha.SCOPES)

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
  def aggregation_service(self):
    return self.compute.instanceGroupManagers

  @property
  def resource_type(self):
    return 'instanceGroupManagers'

  def Display(self, args, resources):
    """Prints the given resources."""
    resources = list(resources)
    super(ListAlpha, self).Display(args, resources)
    if _AutoscalerWithErrorInList(resources):
      log.err.Print('(*) - there are errors in your autoscaling setup, please '
                    'describe the resource to see details')


List.detailed_help = base_classes.GetZonalListerHelp(
    'managed instance groups')
ListAlpha.detailed_help = base_classes.GetMultiScopeListerHelp(
    'managed instance groups', ListAlpha.SCOPES)
