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
"""EntryLink drafting for the dbt -> Dataplex transform.

The functions here construct EntryLink records that capture lineage and
semantic relationships between dbt entries. They are emitted by default;
``transform.GenerateImportFile`` skips them only when
``include_entry_links=False`` (exposed as ``--no-include-entry-links`` on the
``metadata-jobs create`` command). The dbt entry link types (belongs-to,
consumed-by, defines-semantics-for, depends-on, derives-from, materializes-to,
schema-join) are first-party system types under the same environment-specific
system project as the aspect / entry types.

dbt ``relationships`` tests map to ``logical-schema-join`` (undirected, accepts
any Dataplex entry) carrying the required ``schema-join`` aspect -- NOT the
BigQuery-only ``schema-join`` link type, which cannot link dbt entries.

``materializes-to`` links (dbt model/seed/snapshot -> the physical @bigquery
table entry) are emitted only when ``build_entry_links(bigquery_location=...)``
is given the physical entries' Dataplex region -- it is not carried in the
manifest, so callers supply it (see ``transform`` / the command's
``--bigquery-location``). All other edges are derived purely from the manifest.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Set
import hashlib
import re
from typing import Any, TypedDict

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


# One endpoint of an EntryLink. ``name`` and ``type`` are always set; ``path``
# is present only for column-level links, hence total=False. The field names
# mirror the Dataplex wire format (camelCase).
_EntryReference = TypedDict(
    '_EntryReference',
    {
        'name': str,  # resource name of the referenced entry
        'type': str,  # 'SOURCE' | 'TARGET' | 'UNSPECIFIED'
        'path': str,  # column path on the referenced entry (column-level only)
    },
    total=False,
)


# The entry link itself. ``aspects`` is set only for link types that declare
# ``required_aspects`` (e.g. logical-schema-join carries a ``schema-join``
# aspect), hence total=False.
_EntryLinkBody = TypedDict(
    '_EntryLinkBody',
    {
        'name': str,  # fully-qualified entryLink resource name
        'entryLinkType': str,  # fully-qualified entryLinkType resource name
        'entryReferences': list[_EntryReference],
        'aspects': dict[str, Any],
    },
    total=False,
)


# One line of the JSONL import file: a single dbt-derived entry link. Mirrors
# the Dataplex import item shape; the sole key is ``entryLink`` (built by
# ``_entry_link``).
EntryLinkRecord = TypedDict('EntryLinkRecord', {'entryLink': _EntryLinkBody})


def _link_id(
    link_type_short: str,
    source_fully_qualified_name: str,
    target_fully_qualified_name: str,
) -> str:
  digest = hashlib.sha1(
      f'{source_fully_qualified_name}|{target_fully_qualified_name}'.encode(
          'utf-8'
      )
  ).hexdigest()[:16]
  link_type_id = link_type_short.replace('_', '-')
  return f'{link_type_id}-{digest}'


def _entry_link(
    ctx: naming.Context,
    link_type_short: str,
    source_fully_qualified_name: str,
    target_fully_qualified_name: str,
    *,
    source_path: str | None = None,
    target_path: str | None = None,
    aspects: dict[str, Any] | None = None,
    undirected: bool = False,
) -> EntryLinkRecord:
  """Builds one EntryLink record between two entries.

  Args:
    ctx: the naming.Context holding the naming coordinates for this run.
    link_type_short: the short link key (e.g. 'depends_on').
    source_fully_qualified_name: resource name of the SOURCE entry.
    target_fully_qualified_name: resource name of the TARGET entry.
    source_path: optional column path on the source entry.
    target_path: optional column path on the target entry.
    aspects: optional aspect map (key -> {aspectType, data}) attached to the
      link, required by link types that declare ``required_aspects`` (e.g.
      logical-schema-join needs the ``schema-join`` aspect).
    undirected: when True, both references are UNSPECIFIED (the link type is
      undirected, e.g. logical-schema-join); a directed SOURCE/TARGET reference
      would be rejected for an undirected type.

  Returns:
    An EntryLink record.
  """
  entry_link_id = _link_id(
      link_type_short, source_fully_qualified_name, target_fully_qualified_name
  )
  ref_type = 'UNSPECIFIED' if undirected else None
  source_ref: _EntryReference = {
      'name': source_fully_qualified_name,
      'type': ref_type or 'SOURCE',
  }
  target_ref: _EntryReference = {
      'name': target_fully_qualified_name,
      'type': ref_type or 'TARGET',
  }
  if source_path:
    source_ref['path'] = source_path
  if target_path:
    target_ref['path'] = target_path
  entry_link: _EntryLinkBody = {
      'name': (
          f'projects/{ctx.eg_project}/locations/{ctx.eg_location}/'
          f'entryGroups/{ctx.entry_group}/entryLinks/{entry_link_id}'
      ),
      'entryLinkType': ctx.link_type_fqn(link_type_short),
      'entryReferences': [source_ref, target_ref],
  }
  if aspects:
    entry_link['aspects'] = aspects
  return {'entryLink': entry_link}


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
    ctx: naming.Context, manifest: Mapping[str, Any], known_ids: Set[str]
) -> list[EntryLinkRecord]:
  """Emits ``depends-on`` entry links (dependent -> dependency) from parent_map.

  The link is directed source -> target, where "the source entry depends on
  the target entry" (see the ``depends-on`` entryLinkType definition).
  ``parent_map`` maps each node to the nodes it depends on (its parents), so
  the SOURCE is the map key (the dependent) and each TARGET is a value (the
  dependency). Tests are included: a test depends on the model(s) it
  validates, emitted as ``test -> model``.

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
  out: list[EntryLinkRecord] = []
  parent_map = manifest.get(_PARENT_MAP) or {}
  for dependent_uid, dependency_uids in parent_map.items():
    dependent_id = naming.entry_id(dependent_uid)
    if dependent_id not in known_ids:
      continue
    dependent_fully_qualified_name = ctx.entry_name(dependent_id)
    for dependency_uid in dependency_uids:
      dependency_id = naming.entry_id(dependency_uid)
      if dependency_id not in known_ids:
        continue
      out.append(
          _entry_link(
              ctx,
              'depends_on',
              dependent_fully_qualified_name,
              ctx.entry_name(dependency_id),
          )
      )
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
    ctx: naming.Context, manifest: Mapping[str, Any], known_ids: Set[str]
) -> list[EntryLinkRecord]:
  """Model / semantic_model / metric -> dbt group entry."""
  out: list[EntryLinkRecord] = []
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


def _schema_join_aspect(
    ctx: naming.Context,
    source_sql: str,
    source_field: str,
    target_sql: str,
    target_field: str,
) -> dict[str, Any]:
  """Builds the ``schema-join`` aspect required by logical-schema-join links.

  ``logical-schema-join`` declares ``required_aspects: schema-join``, so each
  link carries a single Dataplex-owned ``schema-join`` aspect describing the
  joinable columns (payload follows the aspect type's ``SchemaJoins`` template).
  The ``schema-join`` aspect type is a core 1P type in the same system project
  as the entry link types, so its key / fqn use ``system_project``.

  Args:
    ctx: the naming.Context holding the naming coordinates for this run.
    source_sql: SQL representation (relation name) of the source entity.
    source_field: joinable column on the source entity.
    target_sql: SQL representation (relation name) of the target entity.
    target_field: joinable column on the target entity.

  Returns:
    An aspect map ({aspect_key: {aspectType, data}}) for the link.
  """
  key = f'{ctx.system_project}.{ctx.types_location}.schema-join'
  fqn = (
      f'projects/{ctx.system_project}/locations/{ctx.types_location}/'
      'aspectTypes/schema-join'
  )
  data = {
      'joins': [{
          'source': {'name': source_sql, 'fields': [source_field]},
          'target': {'name': target_sql, 'fields': [target_field]},
          # A dbt `relationships` test asserts a user-authored foreign key.
          'type': 'FOREIGN_KEY',
          'inferenceSource': 'USER',
      }],
      'userManaged': True,
  }
  return {key: {'aspectType': fqn, 'data': data}}


def _emit_schema_join(
    ctx: naming.Context, manifest: Mapping[str, Any], known_ids: Set[str]
) -> list[EntryLinkRecord]:
  """Child model -> parent model, from relationships tests.

  Emitted as a ``logical-schema-join`` link (undirected, accepts any Dataplex
  entry) carrying the required ``schema-join`` aspect. The BigQuery-native
  ``schema-join`` link type is NOT used -- it is restricted to BigQuery/BigLake
  entry types and cannot link dbt entries. The joinable columns live in the
  aspect (source/target fields), NOT as entryReference ``path`` values: dbt
  columns are in the custom ``dbt-schema`` aspect, not a Dataplex-resolvable
  entry path, so a column path would be rejected.

  Args:
    ctx: the naming.Context holding the naming coordinates for this run.
    manifest: the manifest dict.
    known_ids: set of known entry IDs (to filter dependencies that exist).

  Returns:
    A list of logical-schema-join EntryLink records.
  """
  out: list[EntryLinkRecord] = []
  nodes = manifest.get(_NODES) or {}
  model_uid_by_name = _index_uid_by_name(
      nodes, lambda n: n.get('resource_type') == 'model'
  )
  for node in nodes.values():
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
    child_col = kwargs.get('column_name') or None
    parent_col = kwargs.get('field') or None
    aspects = None
    if child_col and parent_col:
      # The schema-join aspect names the joinable columns; use each model's
      # relation_name (SQL representation), falling back to the entry id.
      child_sql = (nodes.get(attached) or {}).get('relation_name') or child_id
      parent_sql = (nodes.get(parent_uid) or {}).get('relation_name') or (
          parent_id
      )
      aspects = _schema_join_aspect(
          ctx, child_sql, child_col, parent_sql, parent_col
      )
    out.append(
        _entry_link(
            ctx,
            'schema_join',
            ctx.entry_name(child_id),
            ctx.entry_name(parent_id),
            aspects=aspects,
            undirected=True,
        )
    )
  return out


def _emit_consumed_by(
    ctx: naming.Context, manifest: Mapping[str, Any], known_ids: Set[str]
) -> list[EntryLinkRecord]:
  """Upstream dbt resource -> exposure entry."""
  out: list[EntryLinkRecord] = []
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
    ctx: naming.Context, manifest: Mapping[str, Any], known_ids: Set[str]
) -> list[EntryLinkRecord]:
  """semantic_model -> its backing model."""
  out: list[EntryLinkRecord] = []
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
    ctx: naming.Context, manifest: Mapping[str, Any], known_ids: Set[str]
) -> list[EntryLinkRecord]:
  """metric or saved_query -> upstream metric / semantic_model."""
  out: list[EntryLinkRecord] = []
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


# dbt resource types that materialize to a physical BigQuery table.
_MATERIALIZED_RESOURCE_TYPES = frozenset(['model', 'seed', 'snapshot'])


def _get_bigquery_entry_name(
    bq_location: str, database: str, schema: str, table: str
) -> str:
  """Returns the @bigquery entry resource name a dbt node materializes to.

  Dataplex auto-catalogs BigQuery tables into the system ``@bigquery`` entry
  group; the entry id is the table's BigQuery resource path. The project may be
  given by id or number -- the dbt node carries the id (``database``). The
  entry's Dataplex region (``bq_location``) is not in the manifest.

  Args:
    bq_location: Dataplex region hosting the @bigquery entries (e.g.
      us-central1).
    database: BigQuery project (dbt ``database``).
    schema: BigQuery dataset (dbt ``schema``).
    table: BigQuery table (dbt ``alias`` / ``name``).

  Returns:
    The @bigquery entry resource name.
  """
  return (
      f'projects/{database}/locations/{bq_location}/entryGroups/@bigquery/'
      # gcloud-disable-gdu-domain
      f'entries/bigquery.googleapis.com/projects/{database}/datasets/{schema}/'
      f'tables/{table}'
  )


def materialized_bigquery_projects(manifest: Mapping[str, Any]) -> set[str]:
  """Returns the BigQuery projects (dbt ``database``) of materialized nodes.

  Used to scope the import job's referencedEntryScopes so materializes-to links
  to physical @bigquery entries in those projects resolve.

  Args:
    manifest: the parsed dbt manifest.json.

  Returns:
    The set of distinct project ids that materialized nodes write to.
  """
  return {
      node['database']
      for node in (manifest.get(_NODES) or {}).values()
      if node.get('resource_type') in _MATERIALIZED_RESOURCE_TYPES
      and node.get('database')
  }


def materialized_bigquery_datasets(
    manifest: dict[str, Any],
) -> set[tuple[str, str]]:
  """Returns the ``(database, schema)`` pairs the materialized nodes write to.

  Args:
    manifest: the parsed dbt manifest.json.

  Returns:
    The set of distinct ``(database, schema)`` pairs of materialized nodes.
  """
  return {
      (node['database'], node['schema'])
      for node in (manifest.get(_NODES) or {}).values()
      if node.get('resource_type') in _MATERIALIZED_RESOURCE_TYPES
      and node.get('database')
      and node.get('schema')
  }


def _emit_materializes_to(
    ctx: naming.Context,
    manifest: Mapping[str, Any],
    known_ids: Set[str],
    bq_location: str,
) -> list[EntryLinkRecord]:
  """Emits materializes-to links from dbt nodes to their @bigquery tables.

  The target is the Dataplex system @bigquery entry for the BigQuery table dbt
  writes; its Dataplex region comes from ``bq_location`` (not in the manifest).
  The physical entry must already be cataloged (BigQuery metadata is auto-
  ingested into Dataplex); if it is absent the import reports that link as an
  error and continues. ``materializes-to`` disables the target permission check,
  so read-only access to the physical table is sufficient.

  Args:
    ctx: the naming.Context holding the naming coordinates for this run.
    manifest: the parsed dbt manifest.json.
    known_ids: set of emitted dbt entry ids.
    bq_location: Dataplex region hosting the @bigquery entries.

  Returns:
    A list of materializes-to EntryLink records.
  """
  out: list[EntryLinkRecord] = []
  for uid, node in (manifest.get(_NODES) or {}).items():
    if node.get('resource_type') not in _MATERIALIZED_RESOURCE_TYPES:
      continue
    d_id = naming.entry_id(uid)
    if d_id not in known_ids:
      continue
    database = node.get('database')
    schema = node.get('schema')
    table = node.get('alias') or node.get('name')
    if not (database and schema and table):
      continue
    out.append(
        _entry_link(
            ctx,
            'materializes_to',
            ctx.entry_name(d_id),
            _get_bigquery_entry_name(bq_location, database, schema, table),
        )
    )
  return out


def build_entry_links(
    ctx: naming.Context,
    manifest: Mapping[str, Any],
    known_ids: Set[str],
    bigquery_location: str | None = None,
) -> list[EntryLinkRecord]:
  """Builds all EntryLink records (lineage + semantic edges).

  NOTE: only called when include_entry_links=True.

  Args:
    ctx: the naming.Context holding the naming coordinates for this run.
    manifest: the parsed dbt manifest.json.
    known_ids: the set of Dataplex entry ids the transform emitted; edges that
      reference an id outside this set are dropped.
    bigquery_location: Dataplex region of the physical @bigquery entries. When
      set, materializes-to links (dbt node -> physical BigQuery table) are
      emitted; when None they are skipped (the region is not in the manifest).

  Returns:
    A list of EntryLink records for the resolvable lineage / semantic edges.
  """
  links: list[EntryLinkRecord] = []
  links.extend(_emit_depends_on(ctx, manifest, known_ids))
  links.extend(_emit_belongs_to(ctx, manifest, known_ids))
  links.extend(_emit_schema_join(ctx, manifest, known_ids))
  links.extend(_emit_consumed_by(ctx, manifest, known_ids))
  links.extend(_emit_defines_semantics_for(ctx, manifest, known_ids))
  links.extend(_emit_derives_from(ctx, manifest, known_ids))
  if bigquery_location:
    links.extend(
        _emit_materializes_to(ctx, manifest, known_ids, bigquery_location)
    )
  return links
