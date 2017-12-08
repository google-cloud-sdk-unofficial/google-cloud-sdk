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

"""A command that lists the resource collections for a given API."""

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.meta import apis


class List(base.ListCommand):
  """List the resource collections for an API."""

  @staticmethod
  def Args(parser):
    base.PAGE_SIZE_FLAG.RemoveFromParser(parser)
    base.URI_FLAG.RemoveFromParser(parser)
    parser.add_argument(
        '--api',
        required=True,
        help='The name of the API to get the collections for.')
    parser.add_argument(
        '--api-version',
        required=True,
        help='The version of the API to get the collections for.')
    parser.display_info.AddFormat("""
      table(
        name:sort=1:label=COLLECTION_NAME,
        path,
        params.join(', ')
      )
    """)

  def Run(self, args):
    return apis.GetAPICollections(args.api, args.api_version)
