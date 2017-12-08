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

"""Implementation of gcloud bigquery datasets list.
"""

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.bigquery import bigquery
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties
from surface import bigquery as commands


class DatasetsList(base.ListCommand):
  """List datasets in the current project."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    base.LIMIT_FLAG.SetDefault(parser, bigquery.DEFAULT_RESULTS_LIMIT)
    parser.add_argument('--all', help='List even hidden datasets.')

  def Collection(self):
    return 'bigquery.datasets'

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace, All the arguments that were provided to this
        command invocation.

    Returns:
      A list of bigquery_messages.DatasetsValueListEntry objects. Each such
      object has the following form:
          {'kind': 'bigquery#dataset',
           'datasetReference': {'projectId': '$PROJ', 'datasetId': '$DS'},
           'id': '$PROJ:$DS'}
    """
    apitools_client = self.context[commands.APITOOLS_CLIENT_KEY]
    bigquery_messages = self.context[commands.BIGQUERY_MESSAGES_MODULE_KEY]
    project_id = properties.VALUES.core.project.Get(required=True)
    return list_pager.YieldFromList(
        apitools_client.datasets,
        bigquery_messages.BigqueryDatasetsListRequest(projectId=project_id),
        limit=args.limit or -1,
        batch_size=None,  # Use server default.
        field='datasets')
