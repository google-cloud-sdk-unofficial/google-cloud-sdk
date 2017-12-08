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

"""List project repositories.
"""

from googlecloudsdk.api_lib.source import source
from googlecloudsdk.calliope import base
from googlecloudsdk.core import list_printer
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.Command):
  """Lists all repositories in a particular project.

  By default, repos in the current project are listed; this can be overridden
  with the gcloud --project flag.
  """

  @staticmethod
  def Args(parser):
    pass

  def Run(self, args):
    """Run the list command."""
    project = source.Project(properties.VALUES.core.project.Get(required=True))
    return project.ListRepos()

  def Display(self, args, repos):
    """This method is called to print the result of the Run() method.

    Args:
      args: The arguments that command was run with.
      repos: The iterator over Repo messages returned from the Run() method.
    """
    list_printer.PrintResourceList('source.jobs.list', repos)
