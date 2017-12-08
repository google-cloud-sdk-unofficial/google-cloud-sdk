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
"""Command for deleting sole-tenancy hosts."""
from googlecloudsdk.api_lib.compute import base_classes


class Delete(base_classes.ZonalDeleter):
  """Delete Google Compute Engine sole-tenancy hosts.

  *{command}* deletes one or more Google Compute Engine
  sole-tenancy hosts. Hosts can be deleted only if they are not
  being used by any virtual machine instances.
  """

  @property
  def service(self):
    return self.compute.hosts

  @property
  def resource_type(self):
    return 'hosts'

  @property
  def custom_prompt(self):
    return ('The following hosts will be deleted. Deleting a host is '
            'irreversible and any data on the host will be lost.')

  @staticmethod
  def Args(parser):
    base_classes.ZonalDeleter.Args(parser, 'compute.hosts')
