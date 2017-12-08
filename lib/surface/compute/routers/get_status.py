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

"""Command for getting the status of routers."""
from googlecloudsdk.api_lib.compute import base_classes


class Describe(base_classes.RegionalDescriber):
  """Get status of a Google Compute Engine router.

  *{command}* displays all runtime data associated with a Google Compute
  Engine router.
  """

  @staticmethod
  def Args(parser):
    # TODO(b/24898638): autocomplete
    # cli = Describe.GetCLIGenerator()
    base_classes.RegionalDescriber.Args(parser, 'compute.routers')

  @property
  def service(self):
    return self.compute.routers

  @property
  def resource_type(self):
    return 'routers'

  @property
  def method(self):
    return 'GetRouterStatus'
