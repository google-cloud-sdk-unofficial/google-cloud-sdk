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
"""List command for Resource Manager Semantic Tag Values."""

from googlecloudsdk.api_lib.resource_manager import semantic_tags
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.resource_manager import endpoint_utils as endpoints
from googlecloudsdk.command_lib.resource_manager.semantic_tags import flags
from googlecloudsdk.command_lib.resource_manager.semantic_tags import utils
from googlecloudsdk.core.resource import resource_projection_spec


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  r"""List Semantic Tag Values.

  `{command}` lists Semantic Tag Values under the specified organization or
  project container. Results can be filtered by `semanticTagKey` using
  `--filter` (or `--key`).

  ## EXAMPLES

  To list all Semantic Tag Values under `organizations/1001` in `global`, run:

    $ {command} --location=global --parent=organizations/1001

  To list predefined Semantic Tag Values in the Google Cloud Semantic Tags
  Catalog for the `environment` key, run:

    $ {command} --location=global --parent=projects/gcp-semantic-tags-catalog \
        --key=environment

  To list Semantic Tag Values under `organizations/1001` filtered to a specific
  Semantic Tag Key, run:

    $ {command} --location=global --parent=organizations/1001 \
        --filter="semanticTagKey=projects/gcp-semantic-tags-catalog/locations/global/semanticTagKeys/costcenter.allocation"
  """

  @staticmethod
  def Args(parser):
    flags.AddLocationArgToParser(parser, required=False, default='global')
    flags.AddParentArgToParser(parser)
    flags.AddKeyArgToParser(
        parser,
        required=False,
        help_text=(
            'Filter results to Semantic Tag Values associated with the'
            ' specified Semantic Tag Key. Accepts the full resource name'
            ' (`projects/gcp-semantic-tags-catalog/locations/{location}/'
            'semanticTagKeys/{key}`) or the key ID shorthand (for example,'
            ' `costcenter.allocation`).'
        ),
    )
    base.SORT_BY_FLAG.RemoveFromParser(parser)
    base.URI_FLAG.RemoveFromParser(parser)
    parser.display_info.AddTransforms(
        {'format_semantic_value': utils.FormatSemanticValue}
    )
    parser.display_info.AddFormat(
        'table('
        'name.basename():label=VALUE_ID, '
        'semanticTagKey.basename():label=KEY, '
        'format_semantic_value():label=VALUE, '
        'description'
        ')'
    )

  def Run(self, args):
    parent = utils.GetParent(args, default_to_catalog=False)
    location = args.location or 'global'
    parent_location = f'{parent}/locations/{location}'

    display_info = args.GetDisplayInfo()
    defaults = resource_projection_spec.ProjectionSpec(
        symbols=display_info.transforms, aliases=display_info.aliases
    )
    rewriter = utils.SemanticTagValuesFilterRewriter(location=location)
    args.filter, server_filter = rewriter.Rewrite(
        args.filter, defaults=defaults
    )

    if args.IsSpecified('key') and args.key:
      if server_filter or rewriter.has_key_filter:
        raise calliope_exceptions.InvalidArgumentException(
            '--key',
            'Cannot specify both `--key` and `semanticTagKey` in `--filter`.',
        )
      normalized_key = utils.NormalizeSemanticTagKey(args.key, location)
      server_filter = f'semantic_tag_key = "{normalized_key}"'

    with endpoints.CrmEndpointOverrides(location):
      return semantic_tags.ListSemanticTagValues(
          parent=parent_location,
          filter_expr=server_filter,
          page_size=args.page_size,
      )
