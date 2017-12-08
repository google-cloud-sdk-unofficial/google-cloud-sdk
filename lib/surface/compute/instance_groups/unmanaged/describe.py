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
"""instance-groups unmanaged describe command."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import instance_groups_utils


class Describe(base_classes.ZonalDescriber):
  """Describe an instance group."""

  @staticmethod
  def Args(parser):
    base_classes.ZonalDescriber.Args(parser)

  @property
  def service(self):
    return self.compute.instanceGroups

  @property
  def resource_type(self):
    return 'instanceGroups'

  def ComputeDynamicProperties(self, args, items):
    return instance_groups_utils.ComputeInstanceGroupManagerMembership(
        compute=self.compute,
        project=self.project,
        http=self.http,
        batch_url=self.batch_url,
        items=items,
        filter_mode=instance_groups_utils.InstanceGroupFilteringMode.ALL_GROUPS)

  detailed_help = {
      'brief': 'Describe an instance group',
      'DESCRIPTION': """\
          *{command}* displays detailed information about a Google Compute
          Engine instance group.
          """,
  }
