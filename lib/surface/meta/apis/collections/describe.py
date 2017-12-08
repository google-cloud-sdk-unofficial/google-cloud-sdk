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

"""A command that describes a resource collection for a given API."""

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.meta import apis


class Describe(base.DescribeCommand):
  """Describe the details of a collection for an API."""

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--api',
        required=True,
        help='The name of the API to get the collections for.')
    parser.add_argument(
        '--api-version',
        required=True,
        help='The version of the API to get the collections for.')
    parser.add_argument(
        'collection',
        help='The name of the collection to get the details of.')

  def Run(self, args):
    return apis.GetAPICollection(args.api, args.api_version, args.collection)
