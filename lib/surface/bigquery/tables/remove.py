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

"""Implementation of gcloud bigquery tables remove.
"""

from apitools.base.py import exceptions

from googlecloudsdk.api_lib.bigquery import bigquery
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io
from surface import bigquery as commands


class TablesRemove(base.Command):
  """Removes a specified table or view.

  The user will be asked to confirm the action unless the --quiet flag is
  specified.
  """

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.add_argument(
        '--ignore-not-found',
        action='store_true',
        help='Terminate without an error if the specified table does not '
        'exist.')
    parser.add_argument(
        'table_or_view', help='The table or view to be removed.')

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace, All the arguments that were provided to this
        command invocation.

    Raises:
      ToolException: if user cancels table removal.
    """
    apitools_client = self.context[commands.APITOOLS_CLIENT_KEY]
    bigquery_messages = self.context[commands.BIGQUERY_MESSAGES_MODULE_KEY]
    resource_parser = self.context[commands.BIGQUERY_REGISTRY_KEY]

    table_reference = resource_parser.Parse(
        args.table_or_view, collection='bigquery.tables')
    if not args.quiet:
      if not console_io.PromptContinue(
          message='About to delete table [{0}].'.format(table_reference)):
        raise calliope_exceptions.ToolException('canceled by user')

    request = bigquery_messages.BigqueryTablesDeleteRequest(
        projectId=table_reference.projectId,
        datasetId=table_reference.datasetId,
        tableId=table_reference.tableId)

    try:
      apitools_client.tables.Delete(request)
    except exceptions.HttpError as server_error:
      try:
        raise bigquery.Error.ForHttpError(server_error)
      except bigquery.NotFoundError:
        if args.ignore_not_found:
          log.status.Print('Table [{0}] did not exist.'.format(table_reference))
        else:
          raise
