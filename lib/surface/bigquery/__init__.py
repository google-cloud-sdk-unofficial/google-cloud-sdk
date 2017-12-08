# Copyright 2014 Google Inc. All Rights Reserved.
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

"""The main command group for gcloud bigquery.
"""

import urlparse
from googlecloudsdk.api_lib.bigquery import bigquery
from googlecloudsdk.calliope import base
from googlecloudsdk.core import apis
from googlecloudsdk.core import properties
from googlecloudsdk.core import resolvers
from googlecloudsdk.core import resources
from googlecloudsdk.core.credentials import store as c_store

SERVICE_NAME = 'bigquery'

BIGQUERY_MESSAGES_MODULE_KEY = 'bigquery-messages-module'
APITOOLS_CLIENT_KEY = 'bigquery-apitools-client'
BIGQUERY_REGISTRY_KEY = 'bigquery-registry'


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Bigquery(base.Group):
  """A group of commands for using BigQuery.
  """

  def Filter(self, context, args):
    """Initialize context for bigquery commands.

    Args:
      context: The current context.
      args: The argparse namespace that was specified on the CLI or API.

    Returns:
      The updated context.
    """
    resources.SetParamDefault(
        api='bigquery', collection=None, param='projectId',
        resolver=resolvers.FromProperty(properties.VALUES.core.project))

    # TODO(user): remove command dependence on these.
    context[BIGQUERY_MESSAGES_MODULE_KEY] = apis.GetMessagesModule(
        'bigquery', 'v2')
    context[APITOOLS_CLIENT_KEY] = apis.GetClientInstance('bigquery', 'v2')
    context[BIGQUERY_REGISTRY_KEY] = resources.REGISTRY

    # Inject bigquery backend params.
    bigquery.Bigquery.SetResourceParser(resources.REGISTRY)
    bigquery.Bigquery.SetApiEndpoint()

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--fingerprint-job-id',
        action='store_true',
        help='Whether to use a job id that is derived from a fingerprint of '
        'the job configuration.')
