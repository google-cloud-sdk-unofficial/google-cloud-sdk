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
"""Command for describing SSL certificates."""
from googlecloudsdk.api_lib.compute import base_classes


class Describe(base_classes.GlobalDescriber):
  """Describe a Google Compute Engine SSL certificate."""

  @staticmethod
  def Args(parser):
    base_classes.GlobalDescriber.Args(parser)

  @property
  def service(self):
    return self.compute.sslCertificates

  @property
  def resource_type(self):
    return 'sslCertificates'


Describe.detailed_help = {
    'brief': 'Describe a Google Compute Engine SSL certificate',
    'DESCRIPTION': """\
        *{command}* displays all data associated with Google Compute
        Engine SSL certificate in a project.
        """,
}
