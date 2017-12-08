# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Command for stopping the update process of managed instance group."""
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags


def _AddArgs(parser, multizonal):
  """Adds args."""
  parser.add_argument('name', help='Managed instance group name.')
  if multizonal:
    scope_parser = parser.add_mutually_exclusive_group()
    flags.AddRegionFlag(
        scope_parser,
        resource_type='instance group manager',
        operation_type='stop proactive update instances',
        explanation=flags.REGION_PROPERTY_EXPLANATION_NO_DEFAULT)
    flags.AddZoneFlag(scope_parser,
                      resource_type='instance group manager',
                      operation_type='stop proactive update instances',
                      explanation=flags.ZONE_PROPERTY_EXPLANATION_NO_DEFAULT)
  else:
    flags.AddZoneFlag(parser,
                      resource_type='instance group manager',
                      operation_type='stop proactive update instances')


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.Hidden
class StopUpdateInstancesAlpha(base_classes.BaseAsyncMutator):
  """Stop current proactive update instances of managed instance group."""

  @staticmethod
  def Args(parser):
    _AddArgs(parser=parser, multizonal=False)

  @property
  def method(self):
    return 'Patch'

  @property
  def service(self):
    return self.compute.instanceGroupManagers

  @property
  def resource_type(self):
    return 'instanceGroupManagers'

  def CreateRequests(self, args):
    group_ref = self.CreateZonalReference(args.name, args.zone)
    service = self.compute.instanceGroupManagers
    request = (self.messages.ComputeInstanceGroupManagersPatchRequest(
        project=self.project,
        zone=group_ref.zone,
        instanceGroupManager=group_ref.Name(),
        instanceGroupManagerResource=(self.messages.InstanceGroupManager(
            updatePolicy=self.messages.InstanceGroupManagerUpdatePolicy(type=(
                self.messages.InstanceGroupManagerUpdatePolicy
                .TypeValueValuesEnum.OPPORTUNISTIC))))))

    return [(service, self.method, request)]
