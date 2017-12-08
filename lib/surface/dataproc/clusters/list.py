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

"""List cluster command."""

from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """View a list of clusters in a project.

  View a list of clusters in a project.

  ## EXAMPLES

  To see the list of all clusters, run:

    $ {command}
  """

  @staticmethod
  def Args(parser):
    base.URI_FLAG.RemoveFromParser(parser)

  def Collection(self):
    return 'dataproc.clusters'

  def Run(self, args):
    client = self.context['dataproc_client']
    messages = self.context['dataproc_messages']

    project = properties.VALUES.core.project.Get(required=True)
    region = self.context['dataproc_region']

    request = messages.DataprocProjectsRegionsClustersListRequest(
        projectId=project, region=region)
    response = client.projects_regions_clusters.List(request)
    return response.clusters


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class ListBeta(List):
  """View a list of clusters in a project.

  View a list of clusters in a project.

  ## EXAMPLES

  To see the list of all clusters, run:

    $ {command}

  To see the list of all clusters with particular labels, run:

    $ {command} --filter='labels.env = staging AND labels.starred'
  """

  def Run(self, args):
    client = self.context['dataproc_client']
    messages = self.context['dataproc_messages']

    project = properties.VALUES.core.project.Get(required=True)
    region = self.context['dataproc_region']

    # Explicitly null out args.filter if present because by default args.filter
    # also acts as a postfilter to the things coming back from the backend
    backend_filter = None
    if args.filter:
      backend_filter = args.filter
      args.filter = None

    request = messages.DataprocProjectsRegionsClustersListRequest(
        projectId=project, region=region, filter=backend_filter)
    response = client.projects_regions_clusters.List(request)
    return response.clusters
