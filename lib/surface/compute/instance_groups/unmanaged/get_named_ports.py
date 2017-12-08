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
"""instance-groups unmanaged get-named-ports command.

It's an alias for the instance-groups get-named-ports command.
"""
from googlecloudsdk.api_lib.compute import instance_groups_utils


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
