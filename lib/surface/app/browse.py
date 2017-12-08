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
  """Open the current app in a web browser.

  """

  detailed_help = {
      'DESCRIPTION': """\
          {description}
          """,
      'EXAMPLES': """\
          To open the default service, run:

              $ {command}

          To open a specific service, run:

              $ {command} --service="myService"

          To open a specific version, run:

              $ {command} --service="myService" --version="v1"
          """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--version',
        '-v',
        help=('The version of the app that should be opened. If not specified, '
              "choose a version based on the service's traffic split."))
    parser.add_argument(
        '--service',
        '-s',
        help=('The service that should be opened. If not specified, use the '
              'default service. May be used in conjunction with `--version`.'))

  def Run(self, args):
    project = properties.VALUES.core.project.Get(required=True)
    browser_dispatcher.BrowseApp(project, args.service, args.version)
