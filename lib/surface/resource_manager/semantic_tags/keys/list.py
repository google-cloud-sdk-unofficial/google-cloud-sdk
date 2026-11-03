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
"""List command for Resource Manager Semantic Tag Keys."""

from googlecloudsdk.api_lib.resource_manager import semantic_tags
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.resource_manager import endpoint_utils as endpoints
from googlecloudsdk.command_lib.resource_manager.semantic_tags import keys_catalog
from googlecloudsdk.command_lib.resource_manager.semantic_tags import utils
from googlecloudsdk.core.resource import resource_projection_spec


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  r"""List Semantic Tag Keys.

  `{command}` lists Semantic Tag Keys in the Google Cloud Semantic Tags Catalog
  (`projects/gcp-semantic-tags-catalog`) for the specified location. Results
  can be filtered by `parentSemanticTagKey` or `keyType` using `--filter` (or
  `--parent-key` for immediate child keys).

  ## EXAMPLES

  To list all Semantic Tag Keys in `global` (default `basic` view), run:

    $ {command} --location=global

  To list all Semantic Tag Keys in `global` including direct child keys
  (`full` view), run:

    $ {command} --location=global --view=full

  To list immediate child Semantic Tag Keys under `placement` in `global`, run:

    $ {command} --location=global --parent-key=placement

  To list only `SCALAR` Semantic Tag Keys in `global`, run:

    $ {command} --location=global --filter="keyType=SCALAR"
  """

  @staticmethod
  def Args(parser):
    keys_catalog.AddLocationArgToParser(
        parser, required=False, default='global'
    )
    parser.add_argument(
        '--parent-key',
        metavar='KEY',
        help=(
            'Filter results to immediate child Semantic Tag Keys of the'
            ' specified parent key. Accepts the key ID (for example,'
            ' `placement`), `semanticTagKeys/{key}`,'
            ' `locations/{location}/semanticTagKeys/{key}`, or the full'
            ' resource name (`projects/gcp-semantic-tags-catalog/locations/'
            '{location}/semanticTagKeys/{key}`). Shorter forms use the'
            ' `--location` value and the Google Cloud Semantic Tags Catalog'
            ' project.'
        ),
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
    base.SORT_BY_FLAG.RemoveFromParser(parser)
    base.URI_FLAG.RemoveFromParser(parser)
    parser.display_info.AddFormat(
        'table('
        'name.basename():label=SEMANTIC_TAG_KEY_ID, '
        'shortId, '
        'keyType, '
        'displayName, '
        'parentSemanticTagKey.basename():label=PARENT_KEY'
        ')'
    )

  def Run(self, args):
    location = args.location or 'global'
    if args.view == 'full' and not args.IsSpecified('format'):
      args.GetDisplayInfo().AddFormat(
          'table('
          'name.basename():label=SEMANTIC_TAG_KEY_ID, '
          'shortId, '
          'keyType, '
          'displayName, '
          'parentSemanticTagKey.basename():label=PARENT_KEY, '
          'childSemanticTagKeys.map().basename().list():label=CHILD_KEYS'
          ')'
      )

    display_info = args.GetDisplayInfo()
    defaults = resource_projection_spec.ProjectionSpec(
        symbols=display_info.transforms, aliases=display_info.aliases
    )
    rewriter = utils.SemanticTagKeysFilterRewriter(location=location)
    args.filter, server_filter = rewriter.Rewrite(
        args.filter, defaults=defaults
    )

    if args.IsSpecified('parent_key'):
      if server_filter or rewriter.has_key_filter:
        raise calliope_exceptions.InvalidArgumentException(
            '--parent-key',
            'Cannot specify both `--parent-key` and `parentSemanticTagKey` in'
            ' `--filter`.',
        )
      parent_key = ''
      if args.parent_key:
        parent_key = keys_catalog.NormalizeSemanticTagKey(
            args.parent_key, location, arg_name='--parent-key'
        )
      server_filter = f'parent_semantic_tag_key = "{parent_key}"'

    with endpoints.CrmEndpointOverrides(location):
      return semantic_tags.ListSemanticTagKeys(
          parent=f'{keys_catalog.GetCatalogParent()}/locations/{location}',
          filter_expr=server_filter,
          view=args.view,
          page_size=args.page_size,
      )
