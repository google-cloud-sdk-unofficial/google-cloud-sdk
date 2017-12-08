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
"""Command for describing networks."""
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import networks_utils


class Describe(base_classes.GlobalDescriber):
  """Describe a Google Compute Engine network."""

  @staticmethod
  def Args(parser):
    base_classes.GlobalDescriber.Args(parser, 'compute.networks')

  @property
  def service(self):
    return self.compute.networks

  @property
  def resource_type(self):
    return 'networks'

  def ComputeDynamicProperties(self, args, items):
    return networks_utils.AddMode(items)


Describe.detailed_help = {
    'brief': 'Describe a Google Compute Engine network',
    'DESCRIPTION': """\
        *{command}* displays all data associated with Google Compute
        Engine network in a project.
        """,
}
