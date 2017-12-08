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
"""Command for deleting unmanaged instance groups."""
from googlecloudsdk.api_lib.compute import base_classes


class Delete(base_classes.ZonalDeleter):
  """Delete Google Compute Engine unmanaged instance groups."""

  @property
  def service(self):
    return self.compute.instanceGroups

  @property
  def resource_type(self):
    return 'instanceGroups'


Delete.detailed_help = {
    'brief': 'Delete Google Compute Engine unmanaged instance groups',
    'DESCRIPTION': """\
        *{command}* deletes one or more Google Compute Engine unmanaged
        instance groups. This command just deletes the instance group and does
        not delete the individual virtual machine instances
        in the instance group.
        For example:

          $ {command} example-instance-group-1 example-instance-group-2 --zone us-central1-a

        The above example deletes two instance groups, example-instance-group-1
        and example-instance-group-2, in the ``us-central1-a'' zone.
        """,
}
