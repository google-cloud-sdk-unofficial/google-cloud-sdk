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
"""Implementation of gcloud vectorsearch collections data-objects query."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from apitools.base.py import encoding
from apitools.base.py import list_pager
from googlecloudsdk.api_lib.vector_search import args as common_args
from googlecloudsdk.api_lib.vector_search import clients
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


@base.ReleaseTracks(base.ReleaseTrack.BETA)
@base.DefaultUniverseOnly
class Query(base.ListCommand):
  """Query data objects from a Vector Search collection."""

  detailed_help = {
      'DESCRIPTION': (
          """
          Query data objects from a Vector Search collection.
      """
      ),
      'EXAMPLES': (
          """
          To query data objects from collection `my-collection` in location `us-central1` with a filter, run:

          $ {command} --collection=my-collection --location=us-central1 --limit=10 --json-filter='{"some_field": {"$eq": "some_value"}}'
      """
      ),
  }

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    common_args.AddDataObjectFlags(parser, 'query')
    common_args.AddOutputFieldsFlags(parser)
    parser.display_info.AddUriFunc(
        lambda r: resources.REGISTRY.Parse(
            r.name,
            collection=common_args.GetDataObjectResourceSpec().collection,
        ).SelfLink()
    )

  def Run(self, args):
    """Run the query command."""
    client = clients.DataObjectsClient(self.ReleaseTrack())
    project = properties.VALUES.core.project.GetOrFail()
    parent = 'projects/{}/locations/{}/collections/{}'.format(
        project, args.location, args.collection
    )

    query_request_body = (
        client.messages.GoogleCloudVectorsearchV1betaQueryDataObjectsRequest()
    )

    if args.json_filter:
      try:
        filter_dict = json.loads(args.json_filter)
        query_request_body.filter = encoding.DictToMessage(
            filter_dict,
            client.messages.GoogleCloudVectorsearchV1betaQueryDataObjectsRequest.FilterValue,
        )
      except json.JSONDecodeError as e:
        raise calliope_exceptions.InvalidArgumentException(
            '--json-filter', f'Invalid JSON: {e}'
        )
      except Exception as e:
        # Catch other potential errors during DictToMessage conversion
        raise calliope_exceptions.InvalidArgumentException(
            '--json-filter', f'Error converting JSON filter to message: {e}'
        )

    if (
        args.output_data_fields
        or args.output_vector_fields
        or args.output_metadata_fields
    ):
      query_request_body.outputFields = common_args.ParseOutputFields(
          args, client
      )

    full_req = client.messages.VectorsearchProjectsLocationsCollectionsDataObjectsQueryRequest(
        parent=parent,
        googleCloudVectorsearchV1betaQueryDataObjectsRequest=query_request_body,
    )

    return list_pager.YieldFromList(
        client.service,
        full_req,
        limit=args.limit,
        batch_size=args.page_size,
        batch_size_attribute=(
            'googleCloudVectorsearchV1betaQueryDataObjectsRequest',
            'pageSize',
        ),
        field='dataObjects',
        method='Query',
        current_token_attribute=(
            'googleCloudVectorsearchV1betaQueryDataObjectsRequest',
            'pageToken',
        ),
        next_token_attribute='nextPageToken',
    )
