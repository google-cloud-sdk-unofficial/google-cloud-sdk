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
"""Command for deleting instances managed by managed instance group."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import arg_parsers


class DeleteInstances(base_classes.BaseAsyncMutator):
  """Delete instances managed by managed instance group."""

  @staticmethod
  def Args(parser):
    parser.add_argument('name', help='Managed instance group name.')
    parser.add_argument(
        '--instances',
        type=arg_parsers.ArgList(min_length=1),
        action=arg_parsers.FloatingListValuesCatcher(),
        metavar='INSTANCE',
        required=True,
        help='Names of instances to delete.')
    utils.AddZoneFlag(
        parser,
        resource_type='instance group manager',
        operation_type='delete instances')

  def method(self):
    return 'DeleteInstances'

  @property
  def service(self):
    return self.compute.instanceGroupManagers

  @property
  def resource_type(self):
    return 'instanceGroupManagers'

  def CreateRequests(self, args):
    ref = self.CreateZonalReference(args.name, args.zone)
    instances_ref = self.CreateZonalReferences(
        args.instances,
        ref.zone,
        resource_type='instances')
    instances = [instance_ref.SelfLink() for instance_ref in instances_ref]
    return [(self.method(),
             self.messages.ComputeInstanceGroupManagersDeleteInstancesRequest(
                 instanceGroupManager=ref.Name(),
                 instanceGroupManagersDeleteInstancesRequest=(
                     self.messages.InstanceGroupManagersDeleteInstancesRequest(
                         instances=instances,
                     )
                 ),
                 project=self.project,
                 zone=ref.zone,
             ))]


DeleteInstances.detailed_help = {
    'brief': 'Delete instances managed by managed instance group.',
    'DESCRIPTION': """
        *{command}* is used to deletes one or more instances from a managed
instance group. Once the instances are deleted, the size of the group is
automatically reduced to reflect the changes.

If you would like to keep the underlying virtual machines but still remove them
from the managed instance group, use the abandon-instances command instead.
""",
}
