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

"""List operation command."""
import json

from googlecloudsdk.api_lib.dataproc import util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties


STATE_MATCHER_MAP = {'active': 'ACTIVE', 'inactive': 'NON_ACTIVE'}
STATE_MATCHER_FILTER = 'operation_state_matcher'
CLUSTER_NAME_FILTER = 'cluster_name'
PROJECT_FILTER = 'project_id'


class List(base.ListCommand):
  """View the list of all operations."""

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To see the list of all operations, run:

            $ {command}

          To see the list of all active operations in a cluster, run:

            $ {command} --state-filter active --cluster my_cluster
          """,
  }

  @staticmethod
  def Args(parser):
    base.URI_FLAG.RemoveFromParser(parser)

    parser.add_argument(
        '--cluster',
        help='Restrict to the operations of this Dataproc cluster.')

    parser.add_argument(
        '--state-filter',
        choices=sorted(STATE_MATCHER_MAP.keys()),
        help='Filter by cluster state. Choices are {0}.'.format(
            sorted(STATE_MATCHER_MAP.keys())))

  def Collection(self):
    return 'dataproc.operations'

  @util.HandleHttpError
  def Run(self, args):
    client = self.context['dataproc_client']
    messages = self.context['dataproc_messages']

    project = properties.VALUES.core.project.Get(required=True)
    region = self.context['dataproc_region']
    name = 'projects/{project}/regions/{region}/operations'.format(
        project=project, region=region)

    filter_dict = dict()
    if args.state_filter:
      filter_dict[STATE_MATCHER_FILTER] = STATE_MATCHER_MAP[args.state_filter]
    if args.cluster:
      filter_dict[CLUSTER_NAME_FILTER] = args.cluster

    request = messages.DataprocProjectsRegionsOperationsListRequest(
        name=name, filter=json.dumps(filter_dict))

    response = client.projects_regions_operations.List(request)
    return response.operations
