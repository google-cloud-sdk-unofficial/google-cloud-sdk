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
"""EntryLink drafting for the dbt -> Dataplex transform (OFF by default).

The functions here construct EntryLink records that capture lineage and
semantic relationships between dbt entries. They are emitted only when
``transform.GenerateImportFile(include_entry_links=True)``. The dbt entry link
types (belongs-to, consumed-by, defines-semantics-for, depends-on, derives-from,
materializes-to, schema-join) are first-party system types under the same
environment-specific system project as the aspect / entry types. Keep links
opt-in since they may not be provisioned in every environment yet.

``materializes-to`` links into the @bigquery entry group are intentionally not
emitted: they require a live `bq` lookup of each dataset's region, which is out
of scope for now. The remaining edges are derived purely from the manifest.
"""

from __future__ import annotations

from collections.abc import Callable
import hashlib
import re
from typing import Any

from googlecloudsdk.command_lib.dataplex.dbt import naming

# Matches a dbt ``ref(...)`` call and captures its quoted arguments. dbt refs
# can be ``ref('model')``, ``ref('package', 'model')`` or ``ref('model',
# version=2)``; the target model is always the last quoted positional argument.
# A ``source(...)`` reference is deliberately not matched (it has no single
# entry counterpart resolvable from the string alone).
_REF_CALL = re.compile(r'ref\(([^)]*)\)')
_QUOTED = re.compile(r"""['"]([^'"]+)['"]""")

# dbt manifest top-level sections this module reads. Each of these (except
# ``parent_map``) holds resources the transform emits as entries; ``parent_map``
# is the generic dependency graph.
_NODES = 'nodes'
_GROUPS = 'groups'
_METRICS = 'metrics'
_EXPOSURES = 'exposures'
_PARENT_MAP = 'parent_map'
_SAVED_QUERIES = 'saved_queries'
_SEMANTIC_MODELS = 'semantic_models'


def LinkTypeFqns(  # pylint: disable=invalid-name
    system_project: str, types_location: str
) -> list[str]:
  """Fully-qualified entryLinkType names for the import job scope.

  Entry link types are core 1P types owned by the system project.

  Args:
    system_project: project hosting the core 1P entry link types.
    types_location: location of the system types (always `global`).

  Returns:
    A list of fully-qualified entryLinkType resource names.
  """
  return [
      f'projects/{system_project}/locations/{types_location}/'
      f'entryLinkTypes/{link_id}'
      for link_id in naming.LINK_TYPE_IDS.values()
  ]


def _link_id(link_type_short: str, source_fqn: str, target_fqn: str) -> str:
  digest = hashlib.sha1(
      f'{source_fqn}|{target_fqn}'.encode('utf-8')
  ).hexdigest()[:16]
  link_type_id = link_type_short.replace('_', '-')
  return f'{link_type_id}-{digest}'


def _entry_link(
    ctx: naming.Context,
    link_type_short: str,
    source_fqn: str,
    target_fqn: str,
    *,
    source_path: str | None = None,
    target_path: str | None = None,
) -> dict[str, Any]:
  """Builds one EntryLink record between two entries.

  Args:
    ctx: the naming.Context holding the naming coordinates for this run.
    link_type_short: the short link key (e.g. 'depends_on').
    source_fqn: resource name of the SOURCE entry.
    target_fqn: resource name of the TARGET entry.
    source_path: optional column path on the source entry.
    target_path: optional column path on the target entry.

  Returns:
    An EntryLink record.
  """
  entry_link_id = _link_id(link_type_short, source_fqn, target_fqn)
  source_ref = {'name': source_fqn, 'type': 'SOURCE'}
  target_ref = {'name': target_fqn, 'type': 'TARGET'}
  if source_path:
    source_ref['path'] = source_path
  if target_path:
    target_ref['path'] = target_path
  return {
      'entryLink': {
          'name': (
              f'projects/{ctx.eg_project}/locations/{ctx.eg_location}/'
              f'entryGroups/{ctx.entry_group}/entryLinks/{entry_link_id}'
          ),
          'entryLinkType': ctx.link_type_fqn(link_type_short),
          'entryReferences': [source_ref, target_ref],
      }
  }


def _parse_ref(s: str | None) -> str | None:
  """Returns the target model name from a dbt ``ref(...)`` expression.

  The model name is the last quoted positional argument -- ``ref('model')``,
  ``ref('package', 'model')`` or ``ref('model', version=...)``. Positional
  arguments always come before keyword arguments, so we stop at the first
  keyword argument; this keeps a quoted keyword value like ``version='1'`` from
  being mistaken for the model name.

  Args:
    s: The raw dbt ``ref(...)`` expression, or None.

  Returns:
    The referenced model name, or None if ``s`` is empty or has no quoted
    positional argument.
  """
  if not s:
    return None
  call = _REF_CALL.search(s)
  if not call:
    return None
  model = None
  for arg in call.group(1).split(','):
    if '=' in arg:  # A keyword argument (e.g. version=1); positionals end here.
      break
    quoted = _QUOTED.search(arg)
    if quoted:
      model = quoted.group(1)
  return model


def _emit_depends_on(
    ctx: naming.Context, manifest: dict[str, Any], known_ids: set[str]
) -> list[dict[str, Any]]:
  """Upstream dbt entry -> downstream dbt entry, from parent_map.

  ``parent_map`` covers every dbt dependency, so some of the directed pairs it
  yields are ALSO emitted as a more specific typed edge elsewhere -- e.g. a
  model feeding an exposure appears here as ``depends-on`` and again in
  ``_emit_consumed_by`` as ``consumed-by`` (likewise ``derives-from`` for
  metrics/saved_queries and ``defines-semantics-for`` for semantic models).
  This overlap is intentional: ``depends-on`` is the generic lineage layer and
  the typed edges are the semantic layer, so a consumer can use whichever it
  wants. The two are distinguished by ``entryLinkType``; a graph consumer that
  ignores the type will see the pair twice and must dedupe by type.

  Args:
    ctx: the naming.Context holding the naming coordinates for this run.
    manifest: the manifest dict.
    known_ids: set of known entry IDs (to filter dependencies that exist).

  Returns:
    A list of EntryLink records.
  """
  out = []
  parent_map = manifest.get(_PARENT_MAP) or {}
  for downstream_uid, upstream_uids in parent_map.items():
    if downstream_uid.startswith('test.'):
      continue
    d_id = naming.entry_id(downstream_uid)
    if d_id not in known_ids:
      continue
    d_fqn = ctx.entry_name(d_id)
    for up_uid in upstream_uids:
      if up_uid.startswith('test.'):
        continue
      u_id = naming.entry_id(up_uid)
      if u_id not in known_ids:
        continue
      out.append(_entry_link(ctx, 'depends_on', ctx.entry_name(u_id), d_fqn))
  return out


def _index_uid_by_name(
    mapping: dict[str, Any] | None,
    predicate: Callable[[dict[str, Any]], bool] = lambda _: True,
) -> dict[str, str]:
  """Maps a resource's short ``name`` to its dbt unique_id.

  Group / model cross-references in the manifest are by short name, so resolve
  them against the actual manifest keys rather than reconstructing the unique_id
  by string formatting (which assumes a fixed ``<type>.<project>.<name>``
  layout and breaks for versioned models, packages, etc.).

  Args:
    mapping: a manifest section mapping unique_id -> resource dict.
    predicate: optional filter on the resource dict; only matching resources are
      indexed.

  Returns:
    A dict of short resource name -> dbt unique_id.
  """
  index = {}
  for uid, node in (mapping or {}).items():
    if not predicate(node):
      continue
    name = node.get('name')
    if name:
      index[name] = uid
  return index


def _node_group(node: dict[str, Any]) -> str | None:
  """Returns the group a node belongs to, declared top-level or under config."""
  return node.get('group') or (node.get('config') or {}).get('group')


def _emit_belongs_to(
    ctx: naming.Context, manifest: dict[str, Any], known_ids: set[str]
) -> list[dict[str, Any]]:
  """Model / semantic_model / metric -> dbt group entry."""
  out = []
  group_uid_by_name = _index_uid_by_name(manifest.get(_GROUPS))
  sources = [
      (_NODES, lambda n: n.get('resource_type') == 'model'),
      (_SEMANTIC_MODELS, lambda _: True),
      (_METRICS, lambda _: True),
  ]
  for top_key, predicate in sources:
    for uid, node in (manifest.get(top_key) or {}).items():
      if not predicate(node):
        continue
      group_name = _node_group(node)
      if not group_name:
        continue
      group_uid = group_uid_by_name.get(group_name)
      if not group_uid:
        continue
      group_id = naming.entry_id(group_uid)
      if group_id not in known_ids:
        continue
      out.append(
          _entry_link(
              ctx,
              'belongs_to',
              ctx.entry_name(naming.entry_id(uid)),
              ctx.entry_name(group_id),
          )
      )
  return out


def _emit_schema_join(
    ctx: naming.Context, manifest: dict[str, Any], known_ids: set[str]
) -> list[dict[str, Any]]:
  """Child model.column -> parent model.column, from relationships tests."""
  out = []
  model_uid_by_name = _index_uid_by_name(
      manifest.get(_NODES), lambda n: n.get('resource_type') == 'model'
  )
  for node in (manifest.get(_NODES) or {}).values():
    if node.get('resource_type') != 'test':
      continue
    tm = node.get('test_metadata') or {}
    if tm.get('name') != 'relationships':
      continue
    kwargs = tm.get('kwargs') or {}
    attached = node.get('attached_node')
    if not attached:
      continue
    parent_name = _parse_ref(kwargs.get('to') or '')
    if not parent_name:
      continue
    parent_uid = model_uid_by_name.get(parent_name)
    if not parent_uid:
      continue
    child_id = naming.entry_id(attached)
    parent_id = naming.entry_id(parent_uid)
    if child_id not in known_ids or parent_id not in known_ids:
      continue
    out.append(
        _entry_link(
            ctx,
            'schema_join',
            ctx.entry_name(child_id),
            ctx.entry_name(parent_id),
            source_path=kwargs.get('column_name') or None,
            target_path=kwargs.get('field') or None,
        )
    )
  return out


def _emit_consumed_by(
    ctx: naming.Context, manifest: dict[str, Any], known_ids: set[str]
) -> list[dict[str, Any]]:
  """Upstream dbt resource -> exposure entry."""
  out = []
  for exp_uid, exposure in (manifest.get(_EXPOSURES) or {}).items():
    exp_id = naming.entry_id(exp_uid)
    if exp_id not in known_ids:
      continue
    exp_fqn = ctx.entry_name(exp_id)
    for up_uid in (exposure.get('depends_on') or {}).get('nodes') or []:
      up_id = naming.entry_id(up_uid)
      if up_id not in known_ids:
        continue
      out.append(
          _entry_link(
              ctx,
              'consumed_by',
              ctx.entry_name(up_id),
              exp_fqn,
          )
      )
  return out


def _emit_defines_semantics_for(
    ctx: naming.Context, manifest: dict[str, Any], known_ids: set[str]
) -> list[dict[str, Any]]:
  """semantic_model -> its backing model."""
  out = []
  for sm_uid, sm in (manifest.get(_SEMANTIC_MODELS) or {}).items():
    sm_id = naming.entry_id(sm_uid)
    if sm_id not in known_ids:
      continue
    for ref_uid in (sm.get('depends_on') or {}).get('nodes') or []:
      ref_id = naming.entry_id(ref_uid)
      if ref_id not in known_ids:
        continue
      out.append(
          _entry_link(
              ctx,
              'defines_semantics_for',
              ctx.entry_name(sm_id),
              ctx.entry_name(ref_id),
          )
      )
  return out


def _emit_derives_from(
    ctx: naming.Context, manifest: dict[str, Any], known_ids: set[str]
) -> list[dict[str, Any]]:
  """metric or saved_query -> upstream metric / semantic_model."""
  out = []
  for top_key in (_METRICS, _SAVED_QUERIES):
    for uid, node in (manifest.get(top_key) or {}).items():
      d_id = naming.entry_id(uid)
      if d_id not in known_ids:
        continue
      d_fqn = ctx.entry_name(d_id)
      for up_uid in (node.get('depends_on') or {}).get('nodes') or []:
        u_id = naming.entry_id(up_uid)
        if u_id not in known_ids:
          continue
        out.append(
            _entry_link(
                ctx,
                'derives_from',
                d_fqn,
                ctx.entry_name(u_id),
            )
        )
  return out


def build_entry_links(
    ctx: naming.Context, manifest: dict[str, Any], known_ids: set[str]
) -> list[dict[str, Any]]:
  """Builds all EntryLink records (lineage + semantic edges).

  NOTE: only called when include_entry_links=True.

  Args:
    ctx: the naming.Context holding the naming coordinates for this run.
    manifest: the parsed dbt manifest.json.
    known_ids: the set of Dataplex entry ids the transform emitted; edges that
      reference an id outside this set are dropped.

  Returns:
    A list of EntryLink records for the resolvable lineage / semantic edges.
  """
  links = []
  links.extend(_emit_depends_on(ctx, manifest, known_ids))
  links.extend(_emit_belongs_to(ctx, manifest, known_ids))
  links.extend(_emit_schema_join(ctx, manifest, known_ids))
  links.extend(_emit_consumed_by(ctx, manifest, known_ids))
  links.extend(_emit_defines_semantics_for(ctx, manifest, known_ids))
  links.extend(_emit_derives_from(ctx, manifest, known_ids))
  return links
