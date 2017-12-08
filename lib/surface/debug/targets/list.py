# Copyright 2016 Google Inc. All Rights Reserved.
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

"""List command for gcloud debug targets command group."""

from googlecloudsdk.api_lib.debug import debug
from googlecloudsdk.calliope import base
from googlecloudsdk.core import list_printer
from googlecloudsdk.core import properties


class List(base.Command):
  """List debug targets."""

  detailed_help = {
      'DESCRIPTION': """\
          This command displays a list of the active debug targets registered
          with the Cloud Debugger.
      """
  }

  def Run(self, args):
    """Run the list command."""
    project_id = properties.VALUES.core.project.Get(required=True)
    debugger = debug.Debugger(project_id)
    return debugger.ListDebuggees()

  def Display(self, args, targets):
    """This method is called to print the result of the Run() method.

    Args:
      args: The arguments that command was run with.
      targets: The value returned from the Run() method.
    """
    list_printer.PrintResourceList('debug.targets', targets)
