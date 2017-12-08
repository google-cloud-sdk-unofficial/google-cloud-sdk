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

"""Command for getting the latest image from a family."""
from googlecloudsdk.api_lib.compute import base_classes


class DescribeFromFamily(base_classes.GlobalDescriber):
  """Describe the latest image from an image family.

  *{command}* looks up the latest image from an image family and runs a describe
  on it.
  """

  @staticmethod
  def Args(parser):
    base_classes.GlobalDescriber.Args(parser, 'compute.images')

  @property
  def service(self):
    return self.compute.images

  @property
  def resource_type(self):
    return 'images'

  @property
  def method(self):
    return 'GetFromFamily'

  def SetNameField(self, ref, request):
    """Sets the field in the request that corresponds to the object name."""
    name = ref.Name()

    if name.startswith('family/'):
      request.family = name[len('family/'):]
    else:
      request.family = name
