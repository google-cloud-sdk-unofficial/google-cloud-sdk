# -*- coding: utf-8 -*- #
# Copyright 2026 Google LLC. All Rights Reserved.
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
"""'developer-knowledge documents search-chunks' command."""

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
class SearchChunks(base.ListCommand):
  """Search for developer knowledge across Google's developer documentation."""

  detailed_help = {
      'DESCRIPTION': """\
          Search for developer knowledge across Google's developer documentation. Return DocumentChunks based on the user's query.

          There may be many chunks from the same Document. To retrieve full documents, use `gcloud alpha developer-knowledge documents describe` with the DocumentChunk.parent returned in the search-chunks results.
          """,
      'EXAMPLES': """\
          To search for document chunks answering a query:

            $ {command} --query="How to create a Cloud Storage bucket?"

          To search for document chunks filtered by data source:

            $ {command} --query="Cloud Functions deployment" --query-filter='data_source = "docs.cloud.google.com"'

          To search with custom pagination:

            $ {command} --query="Compute Engine instances" --page-size=10 --limit=20
          """,
      'API REFERENCE': """\
          This command uses the developerknowledge/v1alpha API. The full
          documentation for this API can be found at:
          https://developers.google.com/knowledge
          """,
  }

  @staticmethod
  def Args(parser):
    base.URI_FLAG.RemoveFromParser(parser)
    base.LIMIT_FLAG.SetDefault(parser, 5)
    parser.add_argument(
        '--query',
        required=True,
        help=(
            'Raw query string provided by the user, such as "How to create a'
            ' Cloud Storage bucket?".'
        ),
    )
    parser.add_argument(
        '--query-filter',
        help=(
            'Apply a strict filter to the search results. Supported filter'
            ' fields: `data_source`, `update_time`, `uri`. Example:'
            ' `data_source = "docs.cloud.google.com"`.'
        ),
    )

  def Run(self, args):
    client = apis.GetClientInstance('developerknowledge', 'v1alpha')
    messages = apis.GetMessagesModule('developerknowledge', 'v1alpha')
    request = messages.DeveloperknowledgeDocumentsSearchDocumentChunksRequest(
        query=args.query,
        filter=args.query_filter,
    )
    return list_pager.YieldFromList(
        client.documents,
        request,
        method='SearchDocumentChunks',
        field='results',
        limit=args.limit,
        batch_size=args.page_size,
        batch_size_attribute='pageSize',
    )
