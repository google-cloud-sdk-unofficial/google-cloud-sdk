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

"""Command for resetting an instance."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.command_lib.compute import flags


class Reset(base_classes.NoOutputAsyncMutator):
  """Reset a virtual machine instance."""

  @staticmethod
  def Args(parser):
    flags.AddZoneFlag(
        parser,
        resource_type='instance',
        operation_type='reset')

    parser.add_argument(
        'name',
        nargs='+',
        completion_resource='compute.instances',
        help='The names of the instances to reset.')

  @property
  def service(self):
    return self.compute.instances

  @property
  def method(self):
    return 'Reset'

  @property
  def resource_type(self):
    return 'instances'

  def CreateRequests(self, args):
    request_list = []
    for name in args.name:
      instance_ref = self.CreateZonalReference(name, args.zone)

      request = self.messages.ComputeInstancesResetRequest(
          instance=instance_ref.Name(),
          project=self.project,
          zone=instance_ref.zone)

      request_list.append(request)
    return request_list

  def Display(self, _, resources):
    # There is no need to display anything when resetting an
    # instance. Instead, we consume the generator returned from Run()
    # to invoke the logic that waits for the reset to complete.
    list(resources)


Reset.detailed_help = {
    'brief': 'Reset a virtual machine instance',
    'DESCRIPTION': """\
        *{command}* is used to perform a hard reset on a Google
        Compute Engine virtual machine.
        """,
}
