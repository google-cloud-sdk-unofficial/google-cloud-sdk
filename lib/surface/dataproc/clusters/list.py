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
  """View a list of all clusters in a project."""

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
  """View a list of all clusters in a project."""

  def Run(self, args):
    client = self.context['dataproc_client']
    messages = self.context['dataproc_messages']

    project = properties.VALUES.core.project.Get(required=True)
    region = self.context['dataproc_region']

    request = messages.DataprocProjectsRegionsClustersListRequest(
        projectId=project, region=region, filter=args.filter)
    response = client.projects_regions_clusters.List(request)
    return response.clusters

List.detailed_help = {
    'DESCRIPTION': '{description}',
    'EXAMPLES': """\
      To see the list of all clusters, run:

        $ {command}
      """,
}
ListBeta.detailed_help = List.detailed_help
