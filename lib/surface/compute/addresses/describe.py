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
"""Command for describing addresses."""
from googlecloudsdk.api_lib.compute import base_classes


class Describe(base_classes.GlobalRegionalDescriber):
  """Display detailed information about an address."""

  @staticmethod
  def Args(parser):
    base_classes.GlobalRegionalDescriber.Args(parser, 'addresses')

  @property
  def global_service(self):
    return self.compute.globalAddresses

  @property
  def regional_service(self):
    return self.compute.addresses

  @property
  def global_resource_type(self):
    return 'globalAddresses'

  @property
  def regional_resource_type(self):
    return 'addresses'

Describe.detailed_help = {
    'brief': 'Display detailed information about an address',
    'DESCRIPTION': """\
        *{command}* displays all data associated with an address in a project.
        """,
    'EXAMPLES': """\
        To get details about a global address, run:

          $ {command} ADDRESS --global

        To get details about a regional address, run:

          $ {command} ADDRESS --region us-central1
        """,
}
