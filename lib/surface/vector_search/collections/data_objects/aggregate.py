# -*- coding: utf-8 -*- #
# Copyright 2025 Google LLC. All Rights Reserved.
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
"""Implementation of gcloud vectorsearch collections data-objects aggregate."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from apitools.base.py import encoding
from googlecloudsdk.api_lib.vector_search import args as common_args
from googlecloudsdk.api_lib.vector_search import clients
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.BETA)
@base.DefaultUniverseOnly
class Aggregate(base.Command):
  """Aggregate data objects."""

  detailed_help = {
      'DESCRIPTION': (
          """
          Aggregate data objects.
      """
      ),
      'EXAMPLES': (
          """
          To aggregate data objects from collection `my-collection` in location `us-central1` in project `my-project` with aggregation method `COUNT`, run:

          $ {command} --collection=my-collection --location=us-central1 --aggregation-method=count --project=my-project
      """
      ),
  }

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    common_args.AddDataObjectFlags(parser, 'aggregate')
    parser.add_argument(
        '--aggregation-method',
        required=True,
        choices={
            'count': 'Count the number of data objects that match the filter.'
        },
        help='The aggregation method to apply to the query.',
    )

  def Run(self, args):
    """Run the aggregate command."""
    client = clients.DataObjectsClient(self.ReleaseTrack())
    project = properties.VALUES.core.project.GetOrFail()
    parent = 'projects/{}/locations/{}/collections/{}'.format(
        project, args.location, args.collection
    )

    aggregate_request_body = (
        client.messages.GoogleCloudVectorsearchV1betaAggregateDataObjectsRequest()
    )

    if args.json_filter:
      try:
        filter_dict = json.loads(args.json_filter)
        aggregate_request_body.filter = encoding.DictToMessage(
            filter_dict,
            client.messages.GoogleCloudVectorsearchV1betaAggregateDataObjectsRequest.FilterValue,
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

    if args.aggregation_method == 'count':
      aggregate_request_body.aggregate = (
          client.messages.GoogleCloudVectorsearchV1betaAggregateDataObjectsRequest.AggregateValueValuesEnum.COUNT
      )

    full_req = client.messages.VectorsearchProjectsLocationsCollectionsDataObjectsAggregateRequest(
        parent=parent,
        googleCloudVectorsearchV1betaAggregateDataObjectsRequest=aggregate_request_body,
    )

    return client.service.Aggregate(full_req)
