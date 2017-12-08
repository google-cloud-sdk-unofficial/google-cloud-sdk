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

"""List project repositories."""

from googlecloudsdk.api_lib.source import source
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """Lists all repositories in a particular project.

  By default, repos in the current project are listed; this can be overridden
  with the gcloud --project flag.
  """

  def Collection(self):
    return 'source.jobs'

  @staticmethod
  def Args(parser):
    base.URI_FLAG.RemoveFromParser(parser)

  def Run(self, args):
    """Run the list command."""
    project = source.Project(properties.VALUES.core.project.Get(required=True))
    return project.ListRepos()
