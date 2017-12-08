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
"""Command for describing forwarding rules."""
from googlecloudsdk.api_lib.compute import base_classes


class Describe(base_classes.GlobalRegionalDescriber):
  """Display detailed information about a forwarding rule."""

  @staticmethod
  def Args(parser):
    base_classes.GlobalRegionalDescriber.Args(parser, 'forwardingRules')

  @property
  def global_service(self):
    return self.compute.globalForwardingRules

  @property
  def regional_service(self):
    return self.compute.forwardingRules

  @property
  def global_resource_type(self):
    return 'globalForwardingRules'

  @property
  def regional_resource_type(self):
    return 'forwardingRules'

Describe.detailed_help = {
    'brief': 'Display detailed information about a forwarding rule',
    'DESCRIPTION': """\
        *{command}* displays all data associated with a forwarding rule
        in a project.
        """,
    'EXAMPLES': """\
        To get details about a global forwarding rule, run:

          $ {command} FORWARDING-RULE --global

        To get details about a regional forwarding rule, run:

          $ {command} FORWARDING-RULE --region us-central1
        """,
}
