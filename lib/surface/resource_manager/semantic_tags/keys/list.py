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

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.resource_manager.semantic_tags import keys_catalog
from googlecloudsdk.core.resource import resource_expr_rewrite
from googlecloudsdk.core.resource import resource_projection_spec


class _ParentKeyFilterRewriter(resource_expr_rewrite.Backend):
  """Filter expression rewriter for ListSemanticTagKeys."""

  def __init__(self, location: str = 'global', **kwargs):
    super().__init__(**kwargs)
    self._location = location
    self.parent_key: str | None = None
    self.has_parent_key_filter: bool = False

  def RewriteTerm(self, key: str, op: str, operand, key_type):
    del key_type  # Unused.
    if key.lower() not in ('parentsemantictagkey', 'parent_semantic_tag_key'):
      return None
    self.has_parent_key_filter = True
    if op != '=' or isinstance(operand, list):
      return None
    raw_val = str(operand)
    if raw_val:
      self.parent_key = keys_catalog.NormalizeSemanticTagKey(
          raw_val, self._location, arg_name='--filter'
      )
    else:
      self.parent_key = ''
    return f'parent_semantic_tag_key = "{self.parent_key}"'


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
            ' specified parent key. Accepts the full resource name'
            ' (`projects/gcp-semantic-tags-catalog/locations/{location}/'
            'semanticTagKeys/{key}`) or the key ID shorthand (for example,'
            ' `placement`).'
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
    rewriter = _ParentKeyFilterRewriter(location=location)
    args.filter, _ = rewriter.Rewrite(args.filter, defaults=defaults)

    expected_parent = rewriter.parent_key
    if args.IsSpecified('parent_key'):
      if rewriter.has_parent_key_filter:
        raise calliope_exceptions.InvalidArgumentException(
            '--parent-key',
            'Cannot specify both `--parent-key` and `parentSemanticTagKey` in'
            ' `--filter`.',
        )
      if not args.parent_key:
        expected_parent = ''
      else:
        expected_parent = keys_catalog.NormalizeSemanticTagKey(
            args.parent_key, location, arg_name='--parent-key'
        )

    entries = keys_catalog.GetHardcodedSemanticTagKeys(location)
    results = []
    for item in entries:
      if expected_parent is not None and (
          item.get('parentSemanticTagKey', '') != expected_parent
      ):
        continue
      results.append(keys_catalog.ApplyView(item, args.view))
    return results
