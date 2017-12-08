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

"""Command for stopping an instance."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.command_lib.compute import flags


class Stop(base_classes.NoOutputAsyncMutator):
  """Stop a virtual machine instance."""

  @staticmethod
  def Args(parser):
    flags.AddZoneFlag(
        parser,
        resource_type='instance',
        operation_type='stop')

    parser.add_argument(
        'name',
        nargs='+',
        completion_resource='compute.instances',
        help='The names of the instances to stop.')

  @property
  def service(self):
    return self.compute.instances

  @property
  def method(self):
    return 'Stop'

  @property
  def resource_type(self):
    return 'instances'

  def CreateRequests(self, args):
    request_list = []
    for name in args.name:
      instance_ref = self.CreateZonalReference(name, args.zone)

      request = self.messages.ComputeInstancesStopRequest(
          instance=instance_ref.Name(),
          project=self.project,
          zone=instance_ref.zone)

      request_list.append(request)
    return request_list

  def Format(self, _):
    # There is no need to display anything when stopping an
    # instance. Instead, format 'none' consume the generator returned from
    # Run() to invoke the logic that waits for the stop to complete.
    return 'none'


Stop.detailed_help = {
    'brief': 'Stop a virtual machine instance',
    'DESCRIPTION': """\
        *{command}* is used stop a Google Compute Engine virtual machine.
        Stopping a VM performs a clean shutdown, much like invoking the shutdown
        functionality of a workstation or laptop. Stopping a VM with a local SSD
        is not supported and will result in an API error.
        """,
}
