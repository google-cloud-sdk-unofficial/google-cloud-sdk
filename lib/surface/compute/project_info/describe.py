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

"""Command for describing the project."""

from googlecloudsdk.api_lib.compute import base_classes


class Describe(base_classes.BaseDescriber):
  """Describe the Google Compute Engine project resource."""

  @staticmethod
  def Args(parser):
    pass

  @property
  def service(self):
    return self.compute.projects

  @property
  def resource_type(self):
    return 'projects'

  def CreateReference(self, args):
    return self.CreateGlobalReference(self.project)

  def SetNameField(self, args, request):
    pass


Describe.detailed_help = {
    'brief': 'Describe the Google Compute Engine project resource',
    'DESCRIPTION': """\
        *{command}* displays all data associated with the Google
        Compute Engine project resource. The project resource contains
        data such as global quotas, common instance metadata, and the
        project's creation time.
        """,
}
