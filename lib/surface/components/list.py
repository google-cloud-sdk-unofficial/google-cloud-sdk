# Copyright 2013 Google Inc. All Rights Reserved.
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

"""The command to list installed/available gcloud components."""

from googlecloudsdk.calliope import base


class List(base.Command):
  """List the status of all Cloud SDK components.

  List all components in the Cloud SDK and provide information such as whether
  the component is installed on the local workstation, whether a newer version
  is available, the size of the component, and the ID used to refer to the
  component in commands.
  """
  detailed_help = {
      'DESCRIPTION': """\
          This command lists all the available components in the Cloud SDK. For
          each component, the command lists the following information:

          * Status on your local workstation: not installed, installed (and
            up to date), and update available (installed, but not up to date)
          * Name of the component (a description)
          * ID of the component (used to refer to the component in other
            [{parent_command}] commands)
          * Size of the component

          In addition, if the `--show-versions` flag is specified, the command
          lists the currently installed version (if any) and the latest
          available version of each individual component.
      """,
      'EXAMPLES': """\
            $ {command}

            $ {command} --show-versions
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--show-versions', required=False, action='store_true',
        help='Show installed and available versions of all components.')

  def Run(self, args):
    """Runs the list command."""
    self.group.update_manager.List(show_versions=args.show_versions)
