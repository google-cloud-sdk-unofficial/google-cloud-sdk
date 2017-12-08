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

"""List captures in a project repository.
"""

from googlecloudsdk.api_lib.source import capture
from googlecloudsdk.calliope import base
from googlecloudsdk.core import list_printer


class List(base.Command):
  """List source captures."""

  detailed_help = {
      'DESCRIPTION': """\
          This command displays a list of the source captures for a project.
          Source captures enable cloud diagnostics tools such as the Cloud
          Debugger to work with a copy of the source code corresponding to a
          deployed binary.
      """
  }

  def Run(self, args):
    """Run the capture command."""
    mgr = capture.CaptureManager()
    return mgr.ListCaptures()

  def Display(self, args, captures):
    """This method is called to print the result of the Run() method.

    Args:
      args: The arguments that command was run with.
      captures: The value returned from the Run() method.
    """
    list_printer.PrintResourceList('source.captures.list', captures)
