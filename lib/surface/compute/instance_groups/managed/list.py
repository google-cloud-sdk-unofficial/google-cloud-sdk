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
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log


# TODO(user): This acts like
# instance-groups list --only-managed
# so they should share code.
@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base_classes.InstanceGroupManagerDynamicProperiesMixin,
           base_classes.ZonalLister):
  """List Google Compute Engine managed instance groups."""

  @property
  def service(self):
    return self.compute.instanceGroupManagers

  @property
  def resource_type(self):
    return 'instanceGroupManagers'

  def Format(self, unused_args):
    return """
          table(
            name,
            location():label=ZONE,
            baseInstanceName,
            size,
            targetSize,
            instanceTemplate.basename(),
            autoscaled
          )
          """

  def GetResources(self, args, errors):
    # GetResources() may set _had_errors True if it encounters errors that don't
    # stop processing. If True then Epilog() below emits one error message.
    self._had_errors = False
    resources = super(List, self).GetResources(args, errors)
    return (resource for resource in resources if resource.zone)

  def Epilog(self, unused_resources_were_displayed):
    if self._had_errors:
      log.err.Print('(*) - there are errors in your autoscaling setup, please '
                    'describe the resource to see details')


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class ListBeta(base_classes.InstanceGroupManagerDynamicProperiesMixin,
               base_classes.MultiScopeLister):
  """List Google Compute Engine managed instance groups."""

  SCOPES = [base_classes.ScopeType.regional_scope,
            base_classes.ScopeType.zonal_scope]

  @staticmethod
  def Args(parser):
    base_classes.MultiScopeLister.AddScopeArgs(parser, ListBeta.SCOPES)

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

  def GetResources(self, args, errors):
    self._had_errors = False
    return super(ListBeta, self).GetResources(args, errors)

  def Epilog(self, unused_resources_were_displayed):
    if self._had_errors:
      log.err.Print('(*) - there are errors in your autoscaling setup, please '
                    'describe the resource to see details')


List.detailed_help = base_classes.GetZonalListerHelp(
    'managed instance groups')
ListBeta.detailed_help = base_classes.GetMultiScopeListerHelp(
    'managed instance groups', ListBeta.SCOPES)
