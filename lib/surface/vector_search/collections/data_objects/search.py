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
"""Implementation of gcloud vectorsearch collections data-objects search."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from apitools.base.py import encoding
from apitools.base.py import list_pager
from googlecloudsdk.api_lib.vector_search import args as common_args
from googlecloudsdk.api_lib.vector_search import clients
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files


SEMANTIC_SEARCH_TASK_TYPE_CHOICES = {
    'classification': 'Specifies that the given text will be classified.',
    'clustering': 'Specifies that the embeddings will be used for clustering.',
    'code-retrieval-query': (
        'Specifies that the embeddings will be used for code retrieval.'
    ),
    'fact-verification': (
        'Specifies that the embeddings will be used for fact verification.'
    ),
    'question-answering': (
        'Specifies that the embeddings will be used for question answering.'
    ),
    'retrieval-document': (
        'Specifies the given text is a document from the corpus being searched.'
    ),
    'retrieval-query': (
        'Specifies the given text is a query in a search/retrieval setting.'
    ),
    'semantic-similarity': 'Specifies the given text will be used for STS.',
}


VECTOR_SEARCH_DISTANCE_METRIC_CHOICES = {
    'dot-product': 'Dot product distance metric.',
    'cosine-distance': 'Cosine distance metric.',
}


@base.ReleaseTracks(base.ReleaseTrack.BETA)
@base.DefaultUniverseOnly
class Search(base.Command):
  """Search data objects from a Vector Search collection."""

  detailed_help = {
      'DESCRIPTION': (
          """
          Search data objects from a Vector Search collection.
      """
      ),
      'EXAMPLES': (
          """
          To search data objects from collection `my-collection` in location `us-central1` using text search and return 10 results, run:

          $ {command} --collection=my-collection --location=us-central1 --text-search-text="test" --text-search-data-fields="text_field" --top-k=10
      """
      ),
  }

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    common_args.AddDataObjectFlags(parser, 'search')
    common_args.AddOutputFieldsFlags(parser)

    parser.add_argument(
        '--top-k',
        type=int,
        help='The number of nearest neighbors to return. Default is 10.',
    )

    search_hint_group = parser.add_mutually_exclusive_group('Search Hint')
    search_hint_group.add_argument(
        '--use-index',
        help="""
        The resource name of the index to use for the search.

        This flag is compatible only with Semantic Search and Vector Search.
        """,
    )
    search_hint_group.add_argument(
        '--use-knn',
        action='store_true',
        help=(
            """If set to true, the search will use the system's default K-Nearest
            Neighbor (KNN) index engine.

            This flag is compatible only with Semantic Search and Vector Search.
            """
        ),
    )

    search_type_group = parser.add_mutually_exclusive_group(
        'Search type', required=True
    )
    semantic_search_group = search_type_group.add_argument_group(
        'Semantic Search'
    )
    vector_search_group = search_type_group.add_argument_group('Vector Search')
    text_search_group = search_type_group.add_argument_group('Text Search')

    # Semantic search flags
    semantic_search_group.add_argument(
        '--semantic-search-text',
        required=True,
        help='The query text for semantic search.',
    )
    semantic_search_group.add_argument(
        '--semantic-search-field',
        required=True,
        help='The vector field to search.',
    )
    semantic_search_group.add_argument(
        '--semantic-task-type',
        required=True,
        choices=SEMANTIC_SEARCH_TASK_TYPE_CHOICES,
        help='The task type of the query embedding for semantic search.',
    )

    # Vector search flags
    vector_search_group.add_argument(
        '--vector-search-field',
        required=True,
        help='The vector field to search.',
    )
    vector_search_group.add_argument(
        '--vector-from-file',
        required=True,
        help=(
            'Path to a JSON file containing dense or sparse vector to search'
            ' with.'
        ),
    )
    vector_search_group.add_argument(
        '--distance-metric',
        choices=VECTOR_SEARCH_DISTANCE_METRIC_CHOICES,
        help=(
            'The distance metric to use for the KNN search. If not specified,'
            ' dot-product will be used as the default.'
        ),
    )

    # Text search flags
    text_search_group.add_argument(
        '--text-search-text',
        required=True,
        help='The query text for text search.',
    )
    text_search_group.add_argument(
        '--text-search-data-fields',
        type=arg_parsers.ArgList(),
        required=True,
        help='The data field names to search.',
        metavar='DATA_FIELD_NAME',
    )

  def _GetOutputFields(self, args, client):
    if (
        args.output_data_fields
        or args.output_vector_fields
        or args.output_metadata_fields
    ):
      return common_args.ParseOutputFields(args, client)
    return None

  def _GetSearchHint(self, args, client):
    if args.use_index:
      return client.messages.GoogleCloudVectorsearchV1betaSearchHint(
          useIndex=client.messages.GoogleCloudVectorsearchV1betaSearchHintIndexHint(
              name=args.use_index
          )
      )
    elif args.use_knn:
      return client.messages.GoogleCloudVectorsearchV1betaSearchHint(
          useKnn=args.use_knn
      )
    return None

  def _GetFilterDict(self, args):
    if args.json_filter:
      try:
        return json.loads(args.json_filter)
      except json.JSONDecodeError as e:
        raise calliope_exceptions.InvalidArgumentException(
            '--json-filter', f'Invalid JSON: {e}'
        )
    return None

  def _BuildSemanticSearchMessage(
      self, args, client, filter_dict, search_hint, output_fields
  ):
    """Builds a SemanticSearch message."""
    semantic_search = (
        client.messages.GoogleCloudVectorsearchV1betaSemanticSearch(
            searchText=args.semantic_search_text,
            searchField=args.semantic_search_field,
            topK=args.top_k,
        )
    )
    if args.semantic_task_type:
      task_type_code_name = args.semantic_task_type.replace('-', '_').upper()
      semantic_search.taskType = client.messages.GoogleCloudVectorsearchV1betaSemanticSearch.TaskTypeValueValuesEnum.lookup_by_name(
          task_type_code_name
      )
    if filter_dict:
      try:
        semantic_search.filter = encoding.DictToMessage(
            filter_dict,
            client.messages.GoogleCloudVectorsearchV1betaSemanticSearch.FilterValue,
        )
      except Exception as e:
        raise calliope_exceptions.InvalidArgumentException(
            '--json-filter', f'Error converting JSON filter to message: {e}'
        )
    if search_hint:
      semantic_search.searchHint = search_hint
    if output_fields:
      semantic_search.outputFields = output_fields
    return semantic_search

  def _FillInVectorFromFile(self, args, vector_search, client):
    try:
      file_content = files.ReadFileContents(args.vector_from_file)
      vector_dict = json.loads(file_content)
      if len(vector_dict) != 1 or not (
          'dense' in vector_dict or 'sparse' in vector_dict
      ):
        raise calliope_exceptions.InvalidArgumentException(
            '--vector-from-file',
            'Vector file must contain exactly one vector field under key'
            ' "dense" or "sparse".',
        )
      if 'dense' in vector_dict:
        vector_search.vector = encoding.DictToMessage(
            vector_dict['dense'],
            client.messages.GoogleCloudVectorsearchV1betaDenseVector,
        )
      elif 'sparse' in vector_dict:
        vector_search.sparseVector = encoding.DictToMessage(
            vector_dict['sparse'],
            client.messages.GoogleCloudVectorsearchV1betaSparseVector,
        )
    except files.Error as e:
      raise calliope_exceptions.InvalidArgumentException(
          '--vector-from-file', f'Could not read file: {e}'
      )
    except json.JSONDecodeError as e:
      raise calliope_exceptions.InvalidArgumentException(
          '--vector-from-file', f'Invalid JSON: {e}'
      )
    except Exception as e:
      raise calliope_exceptions.InvalidArgumentException(
          '--vector-from-file',
          f'Error parsing vector file: {e}',
      )

  def _BuildVectorSearchMessage(
      self, args, client, filter_dict, search_hint, output_fields
  ):
    """Builds a VectorSearch message."""
    vector_search = client.messages.GoogleCloudVectorsearchV1betaVectorSearch(
        searchField=args.vector_search_field,
        topK=args.top_k,
    )
    self._FillInVectorFromFile(args, vector_search, client)
    if args.distance_metric:
      distance_metric_code_name = args.distance_metric.replace('-', '_').upper()
      vector_search.distanceMetric = client.messages.GoogleCloudVectorsearchV1betaVectorSearch.DistanceMetricValueValuesEnum.lookup_by_name(
          distance_metric_code_name
      )
    if filter_dict:
      try:
        vector_search.filter = encoding.DictToMessage(
            filter_dict,
            client.messages.GoogleCloudVectorsearchV1betaVectorSearch.FilterValue,
        )
      except Exception as e:
        raise calliope_exceptions.InvalidArgumentException(
            '--json-filter', f'Error converting JSON filter to message: {e}'
        )

    if search_hint:
      vector_search.searchHint = search_hint
    if output_fields:
      vector_search.outputFields = output_fields
    return vector_search

  def _LogWarningsIfNeeded(self, args):
    """Logs warnings if incompatible flags are used."""
    if args.use_index:
      log.warning(
          'Search hint is not supported for Text Search. Ignoring'
          ' --use-index=%s',
          args.use_index,
      )
    if args.use_knn:
      log.warning(
          'Search hint is not supported for Text Search. Ignoring --use-knn',
      )

  def _BuildTextSearchMessage(self, args, client, output_fields, filter_dict):
    """Builds a TextSearch message."""
    text_search = client.messages.GoogleCloudVectorsearchV1betaTextSearch(
        searchText=args.text_search_text,
        dataFieldNames=args.text_search_data_fields,
        topK=args.top_k,
    )
    if output_fields:
      text_search.outputFields = output_fields
    if filter_dict:
      try:
        text_search.filter = encoding.DictToMessage(
            filter_dict,
            client.messages.GoogleCloudVectorsearchV1betaTextSearch.FilterValue,
        )
      except Exception as e:
        raise calliope_exceptions.InvalidArgumentException(
            '--json-filter', f'Error converting JSON filter to message: {e}'
        )

    return text_search

  def Run(self, args):
    """Run the search command."""
    client = clients.DataObjectsClient(self.ReleaseTrack())
    project = properties.VALUES.core.project.GetOrFail()
    parent = 'projects/{}/locations/{}/collections/{}'.format(
        project, args.location, args.collection
    )

    search_request_body = (
        client.messages.GoogleCloudVectorsearchV1betaSearchDataObjectsRequest()
    )

    output_fields = self._GetOutputFields(args, client)
    search_hint = self._GetSearchHint(args, client)
    filter_dict = self._GetFilterDict(args)

    if (
        args.semantic_search_text
        or args.semantic_search_field
        or args.semantic_task_type
    ):
      search_request_body.semanticSearch = self._BuildSemanticSearchMessage(
          args, client, filter_dict, search_hint, output_fields
      )
    elif args.vector_from_file or args.vector_search_field:
      search_request_body.vectorSearch = self._BuildVectorSearchMessage(
          args, client, filter_dict, search_hint, output_fields
      )
    elif args.text_search_text or args.text_search_data_fields:
      self._LogWarningsIfNeeded(args)
      search_request_body.textSearch = self._BuildTextSearchMessage(
          args, client, output_fields, filter_dict
      )

    full_req = client.messages.VectorsearchProjectsLocationsCollectionsDataObjectsSearchRequest(
        parent=parent,
        googleCloudVectorsearchV1betaSearchDataObjectsRequest=search_request_body,
    )

    return list_pager.YieldFromList(
        client.service,
        full_req,
        batch_size_attribute=(
            'googleCloudVectorsearchV1betaSearchDataObjectsRequest',
            'pageSize',
        ),
        field='results',
        method='Search',
        current_token_attribute=(
            'googleCloudVectorsearchV1betaSearchDataObjectsRequest',
            'pageToken',
        ),
        next_token_attribute='nextPageToken',
    )
