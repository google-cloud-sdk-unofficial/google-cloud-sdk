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

"""The `app instances list` command."""

from googlecloudsdk.api_lib.app import appengine_api_client
from googlecloudsdk.calliope import base

APPENGINE_PATH_START = 'https://appengine.googleapis.com/v1beta5/'


class List(base.ListCommand):
  """List the instances affiliated with the current App Engine project."""

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To list all App Engine instances, run:

              $ {command}

          To list all App Engine instances for a given service, run:

              $ {command} -s myservice

          To list all App Engine instances for a given version, run:

              $ {command} -v v1
          """,
  }

  def Collection(self):
    return 'appengine.instances'

  def GetUriFunc(self):
    def _GetUri(resource):
      # TODO(user): Use parser when instances collection adds simple URIs
      # (b/29539463) and a Get method
      return APPENGINE_PATH_START + resource.instance.name
    return _GetUri

  @staticmethod
  def Args(parser):
    parser.add_argument('--service', '-s',
                        help=('If specified, only list instances belonging to '
                              'the given service.'))
    parser.add_argument('--version', '-v',
                        help=('If specified, only list instances belonging to '
                              'the given version.'))

  def Run(self, args):
    api_client = appengine_api_client.GetApiClient()
    return api_client.GetAllInstances(args.service, args.version)
