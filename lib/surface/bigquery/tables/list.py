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

"""Implementation of gcloud bigquery tables list.
"""

from apitools.base.py import exceptions
from apitools.base.py import list_pager

from googlecloudsdk.api_lib.bigquery import bigquery
from googlecloudsdk.api_lib.bigquery import message_conversions
from googlecloudsdk.calliope import base
from surface import bigquery as commands


class TablesList(base.ListCommand):
  """Lists the name of each table or view in a specified dataset."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    base.FLATTEN_FLAG.RemoveFromParser(parser)
    base.URI_FLAG.RemoveFromParser(parser)
    parser.add_argument(
        'dataset_name',
        help='The dataset whose tables and views are to be listed.')

  def Collection(self):
    return 'bigquery.tables.list'

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespeace, All the arguments that were provided to this
        command invocation.

    Yields:
      TableList.TablesValueListEntry messages.
    """
    apitools_client = self.context[commands.APITOOLS_CLIENT_KEY]
    bigquery_messages = self.context[commands.BIGQUERY_MESSAGES_MODULE_KEY]
    resource_parser = self.context[commands.BIGQUERY_REGISTRY_KEY]
    resource = resource_parser.Parse(
        args.dataset_name, collection='bigquery.datasets')
    reference = message_conversions.DatasetResourceToReference(
        bigquery_messages, resource)
    request = bigquery_messages.BigqueryTablesListRequest(
        projectId=reference.projectId,
        datasetId=reference.datasetId)
    try:
      for resource in list_pager.YieldFromList(
          apitools_client.tables,
          request,
          batch_size=None,  # Use server default.
          field='tables'):
        yield resource
    except exceptions.HttpError as server_error:
      raise bigquery.Error.ForHttpError(server_error)
