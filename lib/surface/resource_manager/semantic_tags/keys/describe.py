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
"""Describe command for Resource Manager Semantic Tag Keys."""

from googlecloudsdk.api_lib.resource_manager import semantic_tags
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.resource_manager import endpoint_utils as endpoints
from googlecloudsdk.command_lib.resource_manager.semantic_tags import keys_catalog


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Describe(base.DescribeCommand):
  r"""Describe a Semantic Tag Key.

  `{command}` describes a Semantic Tag Key in the Google Cloud Semantic Tags
  Catalog (`projects/gcp-semantic-tags-catalog`) given its key ID or full
  resource name.

  ## EXAMPLES

  To describe the `placement.latency-optimized` Semantic Tag Key in `global`
  (default `basic` view), run:

    $ {command} placement.latency-optimized --location=global

  To describe the composite `placement` Semantic Tag Key including its direct
  child keys (`full` view), run:

    $ {command} placement --location=global --view=full
  """

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'key',
        metavar='KEY',
        help=(
            'Semantic Tag Key to describe: its key ID (for example,'
            ' `placement.latency-optimized`), `semanticTagKeys/{key}`,'
            ' `locations/{location}/semanticTagKeys/{key}`, or its full'
            ' resource name (`projects/gcp-semantic-tags-catalog/locations/'
            '{location}/semanticTagKeys/{key}`). Shorter forms use the'
            ' `--location` value and the Google Cloud Semantic Tags Catalog'
            ' project.'
        ),
    )
    keys_catalog.AddLocationArgToParser(
        parser, required=False, default='global'
    )
    parser.add_argument(
        '--view',
        choices=['basic', 'full'],
        default='basic',
        help=(
            'Level of detail to return (`basic` or `full`). `basic` returns'
            ' standard semantic key attributes without child keys; `full`'
            ' additionally populates `childSemanticTagKeys` with direct child'
            ' key resource names.'
        ),
    )

  def Run(self, args):
    full_name, location, _ = keys_catalog.ParseSemanticTagKeyName(args)
    with endpoints.CrmEndpointOverrides(location):
      return semantic_tags.GetSemanticTagKey(full_name, view=args.view)
