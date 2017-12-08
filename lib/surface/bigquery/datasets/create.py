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

"""Implementation of gcloud bigquery datasets create.
"""

from googlecloudsdk.api_lib.bigquery import bigquery
from googlecloudsdk.api_lib.bigquery import bigquery_client_helper
from googlecloudsdk.api_lib.bigquery import message_conversions
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from surface import bigquery as commands


class DatasetsCreate(base.Command):
  """Creates a new dataset.
  """

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.add_argument('--description', help='Description of the dataset.')
    parser.add_argument(
        '--if-exists',
        choices=['fail', 'skip'],
        default='fail',
        help='What to do if the dataset already exists.')
    parser.add_argument(
        'dataset_name', help='The name of the dataset being created.')

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace, All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.

    Raises:
      bigquery.DuplicateError: dataset exists
    """

    apitools_client = self.context[commands.APITOOLS_CLIENT_KEY]
    bigquery_messages = self.context[commands.BIGQUERY_MESSAGES_MODULE_KEY]
    resource_parser = self.context[commands.BIGQUERY_REGISTRY_KEY]
    project_id = properties.VALUES.core.project.Get(required=True)

    resource = resource_parser.Parse(
        args.dataset_name, collection='bigquery.datasets')
    reference = message_conversions.DatasetResourceToReference(
        bigquery_messages, resource)

    if bigquery_client_helper.DatasetExists(
        apitools_client, bigquery_messages, reference):
      message = 'Dataset {0} already exists.'.format(resource)
      if args.if_exists == 'skip':
        log.status.write(message + '\n')
        return
      else:
        raise bigquery.DuplicateError(message, None, None)
    request = bigquery_messages.BigqueryDatasetsInsertRequest(
        dataset=bigquery_messages.Dataset(
            datasetReference=reference,
            description=args.description),
        projectId=project_id)
    try:
      apitools_client.datasets.Insert(request)
    except bigquery.DuplicateError:
      if args.if_exists == 'skip':
        raise
    log.CreatedResource(resource)
