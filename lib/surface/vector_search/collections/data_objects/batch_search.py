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
"""Implementation of gcloud vectorsearch collections data-objects batch-search."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from apitools.base.py import encoding
from googlecloudsdk.api_lib.vector_search import args as common_args
from googlecloudsdk.api_lib.vector_search import clients
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.util import files


@base.ReleaseTracks(base.ReleaseTrack.BETA)
@base.DefaultUniverseOnly
class BatchSearch(base.Command):
  """Batch search data objects from a Vector Search collection."""

  detailed_help = {
      'DESCRIPTION': (
          """
          Batch search data objects from a Vector Search collection.
          Searches can be specified in a JSON file via --searches-from-file.
      """
      ),
      'EXAMPLES': (
          """
          To batch search data objects from collection `my-collection` in location `us-central1` using searches defined in `searches.json`, run:

          $ {command} --collection=my-collection --location=us-central1 --searches-from-file=searches.json

          Example `searches.json`:
          [
            {
              "semanticSearch": {
                "searchText": "sci-fi movie",
                "searchField": "vector1",
                "topK": 10
              }
            },
            {
              "vectorSearch": {
                "searchField": "vector2",
                "topK": 5,
                "vector": { "values": [0.1, 0.2, 0.3] }
              }
            }
          ]
      """
      ),
  }

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    common_args.AddDataObjectFlags(
        parser, 'batch search', include_json_filter=False
    )
    parser.display_info.AddUriFunc(
        lambda r: resources.REGISTRY.Parse(
            r.name,
            collection=common_args.GetDataObjectResourceSpec().collection,
        ).SelfLink()
    )

    parser.add_argument(
        '--searches-from-file',
        required=True,
        help="""Path to a JSON file containing a list of searches.
Each element in list should be a JSON object representing a Search message,
e.g., `{"semanticSearch": {"searchText": "...", "searchField": "..."}}`.
Keys must be camelCase as in API definition.""",
    )

    combine_group = parser.add_argument_group('Combine Results Options')
    combine_group.add_argument(
        '--combine-top-k',
        type=int,
        help='Top K results to return when combining results.',
    )
    combine_group.add_argument(
        '--combine-output-data-fields',
        type=arg_parsers.ArgList(),
        metavar='DATA_OUTPUT_FIELD',
        help='List of data fields to include in combined output.',
    )
    combine_group.add_argument(
        '--combine-output-vector-fields',
        type=arg_parsers.ArgList(),
        metavar='VECTOR_OUTPUT_FIELD',
        help='List of vector fields to include in combined output.',
    )
    combine_group.add_argument(
        '--combine-output-metadata-fields',
        type=arg_parsers.ArgList(),
        metavar='METADATA_OUTPUT_FIELD',
        help='List of metadata fields to include in combined output.',
    )

    ranker_group = combine_group.add_mutually_exclusive_group(
        'Ranker', required=True
    )
    rrf_group = ranker_group.add_argument_group('RRF Ranker')
    rrf_group.add_argument(
        '--rrf-weights',
        type=arg_parsers.ArgList(element_type=float),
        help='RRF weights for combining results.',
        metavar='WEIGHT',
    )
    vertex_ranker_group = ranker_group.add_argument_group('Vertex Ranker')
    vertex_ranker_group.add_argument(
        '--vertex-ranker-query', help='Vertex ranker query', required=True
    )
    vertex_ranker_group.add_argument(
        '--vertex-ranker-model', help='Vertex ranker model', required=True
    )
    vertex_ranker_group.add_argument(
        '--vertex-ranker-title-template', help='Vertex ranker title template'
    )
    vertex_ranker_group.add_argument(
        '--vertex-ranker-content-template',
        help='Vertex ranker content template',
    )

  def _ParseSearchesFromFile(self, args, client):
    """Parses searches from file."""
    try:
      file_content = files.ReadFileContents(args.searches_from_file)
      searches_list = json.loads(file_content)
      searches = []
      for search_dict in searches_list:
        search_message = encoding.DictToMessage(
            search_dict, client.messages.GoogleCloudVectorsearchV1betaSearch
        )
        searches.append(search_message)
      return searches
    except Exception as e:
      raise calliope_exceptions.InvalidArgumentException(
          '--searches-from-file',
          f'Error reading or parsing searches file: {e}',
      )

  def _BuildCombineOptions(self, args, client):
    """Builds combine options."""
    combine_options = (
        client.messages.GoogleCloudVectorsearchV1betaBatchSearchDataObjectsRequestCombineResultsOptions()
    )
    if args.combine_top_k:
      combine_options.topK = args.combine_top_k
    if (
        args.combine_output_data_fields
        or args.combine_output_vector_fields
        or args.combine_output_metadata_fields
    ):
      combine_options.outputFields = (
          client.messages.GoogleCloudVectorsearchV1betaOutputFields()
      )
      if args.combine_output_data_fields:
        combine_options.outputFields.dataFields = (
            args.combine_output_data_fields
        )
      if args.combine_output_vector_fields:
        combine_options.outputFields.vectorFields = (
            args.combine_output_vector_fields
        )
      if args.combine_output_metadata_fields:
        combine_options.outputFields.metadataFields = (
            args.combine_output_metadata_fields
        )
    return combine_options

  def _BuildRanker(self, args, client):
    """Builds ranker."""
    if args.rrf_weights:
      return client.messages.GoogleCloudVectorsearchV1betaRanker(
          rrf=client.messages.GoogleCloudVectorsearchV1betaReciprocalRankFusion(
              weights=args.rrf_weights
          )
      )
    elif args.vertex_ranker_query:
      return client.messages.GoogleCloudVectorsearchV1betaRanker(
          vertex=client.messages.GoogleCloudVectorsearchV1betaVertexRanker(
              query=args.vertex_ranker_query,
              model=args.vertex_ranker_model,
              titleTemplate=args.vertex_ranker_title_template,
              contentTemplate=args.vertex_ranker_content_template,
          )
      )

  def Run(self, args):
    """Run the batch-search command."""
    client = clients.DataObjectsClient(self.ReleaseTrack())
    project = properties.VALUES.core.project.GetOrFail()
    parent = 'projects/{}/locations/{}/collections/{}'.format(
        project, args.location, args.collection
    )

    batch_search_request_body = (
        client.messages.GoogleCloudVectorsearchV1betaBatchSearchDataObjectsRequest()
    )

    if args.searches_from_file:
      batch_search_request_body.searches = self._ParseSearchesFromFile(
          args, client
      )

    combine_options = self._BuildCombineOptions(args, client)

    if args.rrf_weights or args.vertex_ranker_query:
      combine_options.ranker = self._BuildRanker(args, client)
      batch_search_request_body.combine = combine_options

    full_req = client.messages.VectorsearchProjectsLocationsCollectionsDataObjectsBatchSearchRequest(
        parent=parent,
        googleCloudVectorsearchV1betaBatchSearchDataObjectsRequest=batch_search_request_body,
    )

    return client.service.BatchSearch(full_req)
