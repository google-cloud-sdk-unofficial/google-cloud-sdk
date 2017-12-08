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

"""The Browse command."""


from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.app import browser_dispatcher
from googlecloudsdk.core import properties


class Browse(base.Command):
  """Open the specified versions in a browser."""

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To show version `v1` for the default service in the browser, run:

              $ {command} v1

          To show version `v1` of a specific service in the browser, run:

              $ {command} v1 --service="myService"

          To show multiple versions side-by-side, run:

              $ {command} v1 v2 --service="myService"
          """,
  }

  @staticmethod
  def Args(parser):
    versions = parser.add_argument('versions', nargs='+',
                                   help='The versions to open.')
    versions.detailed_help = (
        'The versions to open (optionally filtered by the --service flag).')
    parser.add_argument('--service', '-s',
                        help=('If specified, only open versions from the '
                              'given service. If not specified, use the '
                              'default service.'))

  def Run(self, args):
    project = properties.VALUES.core.project.Get(required=True)
    for version in args.versions:
      browser_dispatcher.BrowseApp(project, args.service, version)
