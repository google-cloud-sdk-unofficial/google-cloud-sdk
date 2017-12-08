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

"""Implementation of gcloud bigquery datasets patch.
"""

from googlecloudsdk.api_lib.bigquery import message_conversions
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from surface import bigquery as commands


class DatasetsPatch(base.Command):
  """Updates the description of a dataset.
  """

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.add_argument('--description', help='Description of the dataset.')
    parser.add_argument('dataset_name', help='The name of the dataset.')

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespeace, All the arguments that were provided to this
        command invocation.

    Returns:
      None
    """
    apitools_client = self.context[commands.APITOOLS_CLIENT_KEY]
    bigquery_messages = self.context[commands.BIGQUERY_MESSAGES_MODULE_KEY]
    resource_parser = self.context[commands.BIGQUERY_REGISTRY_KEY]
    resource = resource_parser.Parse(
        args.dataset_name, collection='bigquery.datasets')
    reference = message_conversions.DatasetResourceToReference(
        bigquery_messages, resource)
    request = bigquery_messages.BigqueryDatasetsPatchRequest(
        dataset=bigquery_messages.Dataset(
            datasetReference=bigquery_messages.DatasetReference(
                projectId=reference.projectId, datasetId=reference.datasetId),
            description=args.description),
        projectId=reference.projectId,
        datasetId=reference.datasetId)
    apitools_client.datasets.Patch(request)
    log.UpdatedResource(resource)
