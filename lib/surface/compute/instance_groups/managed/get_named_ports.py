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
"""instance-groups managed get-named-ports command.

It's an alias for the instance-groups get-named-ports command.
"""
from googlecloudsdk.api_lib.compute import instance_groups_utils
from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.GA)
class GetNamedPorts(instance_groups_utils.InstanceGroupGetNamedPortsBase):

  @staticmethod
  def Args(parser):
    instance_groups_utils.InstanceGroupGetNamedPortsBase.AddArgs(
        parser=parser, multizonal=False)

  def Run(self, args):
    """Retrieves response with named ports."""
    group_ref = self.CreateZonalReference(args.name, args.zone)
    return instance_groups_utils.OutputNamedPortsForGroup(
        group_ref, self.compute_client)


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class GetNamedPortsAlpha(
    instance_groups_utils.InstanceGroupGetNamedPortsBase):

  @staticmethod
  def Args(parser):
    instance_groups_utils.InstanceGroupGetNamedPortsBase.AddArgs(
        parser=parser, multizonal=True)

  def Run(self, args):
    """Retrieves response with named ports."""
    group_ref = instance_groups_utils.CreateInstanceGroupReference(
        scope_prompter=self, compute=self.compute, resources=self.resources,
        name=args.name, region=args.region, zone=args.zone,
        zonal_resource_type='instanceGroups',
        regional_resource_type='regionInstanceGroups')
    return instance_groups_utils.OutputNamedPortsForGroup(
        group_ref, self.compute_client)


GetNamedPorts.detailed_help = {
    'brief': ('Lists the named ports for a managed instance group'),
    'DESCRIPTION': """\
Named ports are key:value pairs metadata representing the service name and the
port that it's running on. Named ports can be assigned to an instance group,
which indicates that the service is available on all instances in the group.
This information is used by the HTTP Load Balancing service.

For example, to list named ports (name and port tuples) for a managed instance
group:

  $ {command} example-instance-group --zone us-central1-a

The above example lists named ports assigned to an instance group named
``example-instance-group'' in the ``us-central1-a'' zone.
""",
}
GetNamedPortsAlpha.detailed_help = GetNamedPorts.detailed_help
