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
from googlecloudsdk.command_lib.compute.instances import flags as instance_flags


class Reset(base_classes.NoOutputAsyncMutator):
  """Reset a virtual machine instance."""

  @staticmethod
  def Args(parser):
    instance_flags.INSTANCES_ARG.AddArgument(parser)

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
    instance_refs = instance_flags.INSTANCES_ARG.ResolveAsResource(
        args, self.resources, scope_lister=flags.GetDefaultScopeLister(
            self.compute_client, self.project))
    request_list = []
    for instance_ref in instance_refs:
      request = self.messages.ComputeInstancesResetRequest(
          instance=instance_ref.Name(),
          project=self.project,
          zone=instance_ref.zone)

      request_list.append(request)
    return request_list


Reset.detailed_help = {
    'brief': 'Reset a virtual machine instance',
    'DESCRIPTION': """\
        *{command}* is used to perform a hard reset on a Google
        Compute Engine virtual machine.
        """,
}
