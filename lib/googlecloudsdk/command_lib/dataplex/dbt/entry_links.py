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
``metadata-jobs create`` command). The dbt entry link types (represents,
depends-on-lineage-imported, depends-on-imported) are first-party system types
under the corresponding environment-specific system project (e.g.,
dataplex-staging-types), which is separate from the project hosting the dbt
aspect / entry types (e.g., dataplex-staging-3p-types).

``represents`` links are used for both:
1. Physical mapping: dbt model/seed/snapshot ->
   the physical @bigquery table entry. These are emitted only when
   ``build_entry_links(linkable_datasets=...)`` names the datasets to link.
   Entry links are same-region, so the @bigquery entries are named in the
   import location (``ctx.eg_location``); a link only resolves for a dataset
   that actually lives there, so the caller passes the set of co-located
   datasets.
2. Semantic mapping: dbt semantic model -> dbt model.

All other edges (lineage and external consumption) are derived purely from the
manifest.
"""

from __future__ import annotations

import collections
from collections import abc
import hashlib
from typing import Any, TypedDict

from googlecloudsdk.command_lib.dataplex.dbt import entry_builders
from googlecloudsdk.command_lib.dataplex.dbt import naming

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
_SOURCES = 'sources'


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
  # Several short keys share one consolidated type id (materializes_to and
  # defines_semantics_for are both `represents`), so dedupe before scoping.
  return [
      f'projects/{system_project}/locations/{types_location}/'
      f'entryLinkTypes/{link_id}'
      for link_id in sorted(set(naming.LINK_TYPE_IDS.values()))
  ]


def LinkAspectTypeFqns(  # pylint: disable=invalid-name
    system_project: str, types_location: str
) -> list[str]:
  """Fully-qualified aspectType names the entry links carry, for the job scope.

  A link type that declares ``required_aspects`` carries that aspect on every
  link, and the import job only accepts it when the aspect type is in scope.

  Args:
    system_project: project hosting the core 1P aspect types.
    types_location: location of the system types (always `global`).

  Returns:
    A list of fully-qualified aspectType resource names.
  """
  return [
      f'projects/{system_project}/locations/{types_location}/'
      'aspectTypes/schema-join'
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
# ``required_aspects`` (e.g. schema-join carries a ``schema-join`` aspect),
# hence total=False.
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
  link_type_id = naming.LINK_TYPE_IDS[link_type_short]
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
      link, required by link types that declare ``required_aspects``.
    undirected: when True, both references are UNSPECIFIED (the link type is
      undirected); a directed SOURCE/TARGET reference would be rejected for an
      undirected type.

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


def _sql_name(node: dict[str, Any]) -> str:
  """Constructs the fully qualified SQL path (database.schema.table) for a node.

  It dynamically resolves the physical table name based on the dbt relation_name
  if present, falling back to reconstructing it from database, schema, and
  table fields (alias/identifier/name) if relation_name is absent.

  Examples:
    - With relation_name:
      {"relation_name": "`myDb`.`mySchema`.`myTable`"} ->
      "`myDb`.`mySchema`.`myTable`"
    - Reconstructed model with alias:
      {"database": "db", "schema": "sc", "alias": "orders_v2"} ->
      "`db`.`sc`.`orders_v2`"
    - Reconstructed source with identifier:
      {"schema": "raw", "identifier": "events_raw"} -> "`raw`.`events_raw`"
    - Reconstructed fallback:
      {"name": "my_table"} -> "`my_table`"

  Args:
    node: The dbt manifest node dictionary (representing a model, source, etc.).

  Returns:
    The constructed SQL name string, or an empty string if table name cannot be
    found.
  """
  # Prefer relation_name as it is dbt's authoritative, adapter-rendered
  # relation name.
  relation_name = node.get('relation_name')
  if relation_name:
    return relation_name.strip()

  # Fallback: Reconstruct if relation_name is absent.
  database = node.get('database')
  schema = node.get('schema')
  table = node.get('alias') or node.get('identifier') or node.get('name')
  if database and schema and table:
    return f'`{database}`.`{schema}`.`{table}`'
  elif schema and table:
    return f'`{schema}`.`{table}`'

  return f'`{table}`' if table else ''


def _emit_depends_on(
    ctx: naming.Context, manifest: abc.Mapping[str, Any], known_ids: set[str]
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


def _index_uid_by_key(
    mapping: dict[str, Any] | None,
    key_fn: abc.Callable[[dict[str, Any]], Any],
    predicate: abc.Callable[[dict[str, Any]], bool] = lambda _: True,
) -> dict[Any, str]:
  """Indexes a mapping of unique_id -> resource by a custom key.

  If multiple resources produce the same key, that key is marked as ambiguous
  and is excluded from the final index.

  Args:
    mapping: A dictionary of unique_id -> resource dict.
    key_fn: A function that takes a resource dict and returns the index key.
      Must return a hashable value. If it returns None, the resource is skipped.
    predicate: An optional filter function that takes a resource dict and
      returns True if it should be indexed.

  Returns:
    A dictionary of key -> unique_id.
  """
  index = {}
  ambiguous = set()
  for uid, node in (mapping or {}).items():
    if not predicate(node):
      continue
    key = key_fn(node)
    if key is None:
      continue
    if key in index:
      ambiguous.add(key)
    else:
      index[key] = uid
  for key in ambiguous:
    del index[key]
  return index


def _emit_consumed_by(
    ctx: naming.Context, manifest: abc.Mapping[str, Any], known_ids: set[str]
) -> list[EntryLinkRecord]:
  """exposure entry -> Upstream dbt resource (depends-on-imported)."""
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
              exp_fqn,
              ctx.entry_name(up_id),
          )
      )
  return out


def _emit_defines_semantics_for(
    ctx: naming.Context, manifest: abc.Mapping[str, Any], known_ids: set[str]
) -> list[EntryLinkRecord]:
  """Emits represents links from semantic models to their backing model.

  A semantic model represents exactly one model, which dbt names outright as
  ``model: ref('orders')``. Fanning out over ``depends_on`` instead would claim
  the semantic model represents every node it touches -- a filter referencing a
  second model, say -- so only the declared model is linked. This is the same
  resolution ``entry_builders`` uses to pick the semantic model's parent entry.

  Args:
    ctx: the naming.Context holding the naming coordinates for this run.
    manifest: the parsed dbt manifest.json.
    known_ids: the set of Dataplex entry ids the transform emitted.

  Returns:
    One represents link per semantic model whose backing model resolves.
  """
  out: list[EntryLinkRecord] = []
  model_uid_by_name = entry_builders.model_uids_by_name(
      manifest.get(_NODES) or {}
  )
  for sm_uid, sm in (manifest.get(_SEMANTIC_MODELS) or {}).items():
    sm_id = naming.entry_id(sm_uid)
    if sm_id not in known_ids:
      continue
    model_uid = entry_builders.described_model(sm, model_uid_by_name)
    if not model_uid:
      continue
    model_id = naming.entry_id(model_uid)
    if model_id not in known_ids:
      continue
    out.append(
        _entry_link(
            ctx,
            'defines_semantics_for',
            ctx.entry_name(sm_id),
            ctx.entry_name(model_id),
        )
    )
  return out


def _emit_derives_from(
    ctx: naming.Context, manifest: abc.Mapping[str, Any], known_ids: set[str]
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


# DBT resource types that materialize to a physical BigQuery table.
_MATERIALIZED_RESOURCE_TYPES = frozenset(['model', 'seed', 'snapshot'])

# An `ephemeral` model is inlined into its dependents as a CTE and never becomes
# a relation so it shouldn't emit a represents link.
_EPHEMERAL_MATERIALIZATION = 'ephemeral'


def _materializes_to_bigquery(node: dict[str, Any]) -> bool:
  """Whether a dbt node becomes a physical BigQuery relation."""
  if node.get('resource_type') not in _MATERIALIZED_RESOURCE_TYPES:
    return False
  materialized = (node.get('config') or {}).get('materialized')
  return str(materialized or '').strip().lower() != _EPHEMERAL_MATERIALIZATION


def _source_key(src: dict[str, Any]) -> tuple[str, str] | None:
  src_name = src.get('source_name')
  tbl_name = src.get('name')
  return (src_name, tbl_name) if src_name and tbl_name else None


def _emit_schema_join(
    ctx: naming.Context, manifest: abc.Mapping[str, Any], known_ids: set[str]
) -> list[EntryLinkRecord]:
  """Child model -> parent model or source, from relationships tests.

  Emitted as a ``schema-join`` link (undirected) carrying the required
  ``schema-join`` aspect. The joinable columns live in that aspect
  (source/target fields) rather than as entryReference ``path`` values, which
  an undirected reference does not accept.

  A test that does not name both columns is skipped rather than emitted without
  the aspect, which the link type would reject.

  Args:
    ctx: the naming.Context holding the naming coordinates for this run.
    manifest: the manifest dict.
    known_ids: set of known entry IDs (to filter dependencies that exist).

  Returns:
    A list of schema-join EntryLink records.
  """
  out: list[EntryLinkRecord] = []
  nodes = manifest.get(_NODES) or {}
  sources = manifest.get(_SOURCES) or {}

  # Index models by name (filtering for materialized resources)
  models_by_name = _index_uid_by_key(
      nodes,
      key_fn=lambda n: n.get('name'),
      predicate=lambda n: n.get('resource_type')
      in _MATERIALIZED_RESOURCE_TYPES,
  )

  # Index sources by (source_name, table_name)
  sources_by_name = _index_uid_by_key(
      sources,
      key_fn=_source_key,
  )

  grouped_joins: dict[tuple[str, str], list[dict[str, Any]]] = (
      collections.defaultdict(list)
  )

  for test_node in nodes.values():
    if test_node.get('resource_type') != 'test':
      continue
    test_metadata = test_node.get('test_metadata') or {}
    if test_metadata.get('name') != 'relationships':
      continue

    kwargs = test_metadata.get('kwargs') or {}
    to_expr = kwargs.get('to')
    target_field = kwargs.get('field')
    source_field = test_node.get('column_name') or kwargs.get('column_name')

    if not (to_expr and target_field and source_field):
      continue

    target_uid = None
    ref_model = naming.parse_ref(to_expr)
    if ref_model:
      target_uid = models_by_name.get(ref_model)
    else:
      ref_source = naming.parse_source(to_expr)
      if ref_source:
        target_uid = sources_by_name.get(ref_source)

    if not target_uid:
      continue

    source_uid = test_node.get('attached_node')
    if not source_uid:
      continue

    # Sort the unique IDs before lowercasing (converting to entry IDs) to
    # ensure case-sensitive sorting order remains stable across re-imports.
    sorted_uids = sorted([source_uid, target_uid])
    first_entry_id = naming.entry_id(sorted_uids[0])
    second_entry_id = naming.entry_id(sorted_uids[1])

    if first_entry_id not in known_ids or second_entry_id not in known_ids:
      continue

    source_node = nodes.get(source_uid) or sources.get(source_uid)
    target_node = nodes.get(target_uid) or sources.get(target_uid)

    if not (source_node and target_node):
      continue

    source_sql = _sql_name(source_node)
    target_sql = _sql_name(target_node)

    if not (source_sql and target_sql):
      continue

    pair = (first_entry_id, second_entry_id)
    join_entry = {
        'source': {
            'name': source_sql,
            'fields': [source_field],
        },
        'target': {
            'name': target_sql,
            'fields': [target_field],
        },
        'type': 'FOREIGN_KEY',
        'inferenceSource': 'USER',
    }

    if join_entry not in grouped_joins[pair]:
      grouped_joins[pair].append(join_entry)

  for (first_entry_id, second_entry_id), joins in grouped_joins.items():
    first_entry_fqn = ctx.entry_name(first_entry_id)
    second_entry_fqn = ctx.entry_name(second_entry_id)
    # The columns live in the aspect rather than as entryReference path values
    # because an undirected reference (which schema-join uses) does not accept
    # a path.
    # Additionally, this aspect is mandatory because the schema-join
    # link type declares required_aspects: schema-join, and a link without
    # it is rejected by Dataplex.
    aspect_data = {
        'joins': joins,
        'userManaged': True,
    }

    aspects = {
        ctx.schema_join_key(): {
            'aspectType': ctx.schema_join_fqn(),
            'data': aspect_data,
        }
    }

    out.append(
        _entry_link(
            ctx,
            'schema_join',
            first_entry_fqn,
            second_entry_fqn,
            aspects=aspects,
            undirected=True,
        )
    )
  return out


def _get_bigquery_entry_name(
    location: str, database: str, schema: str, table: str
) -> str:
  """Returns the @bigquery entry resource name a dbt node materializes to.

  Dataplex auto-catalogs BigQuery tables into the system ``@bigquery`` entry
  group; the entry id is the table's BigQuery resource path. The project may be
  given by id or number -- the dbt node carries the id (``database``).

  Args:
    location: Dataplex region of the @bigquery entry. Entry links are
      same-region, so this is the import location (the dbt entries' region); a
      link only resolves when the table's dataset actually lives there.
    database: BigQuery project (dbt ``database``).
    schema: BigQuery dataset (dbt ``schema``).
    table: BigQuery table (dbt ``alias`` / ``name``).

  Returns:
    The @bigquery entry resource name.
  """
  return (
      f'projects/{database}/locations/{location}/entryGroups/@bigquery/'
      # gcloud-disable-gdu-domain
      f'entries/bigquery.googleapis.com/projects/{database}/datasets/{schema}/'
      f'tables/{table}'
  )


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
      if _materializes_to_bigquery(node)
      and node.get('database')
      and node.get('schema')
  }


def _emit_materializes_to(
    ctx: naming.Context,
    manifest: abc.Mapping[str, Any],
    known_ids: set[str],
    linkable_datasets: set[tuple[str, str]],
) -> list[EntryLinkRecord]:
  """Emits represents (physical) links from dbt nodes to their @bigquery tables.

  The target is the Dataplex system @bigquery entry for the BigQuery table dbt
  writes. Entry links are same-region, so the @bigquery entry is named in the
  import location (``ctx.eg_location``) -- a link only resolves when the table's
  dataset actually lives there, hence the ``linkable_datasets`` filter. The
  physical entry must already be cataloged (BigQuery metadata is auto-ingested
  into Dataplex); if it is absent the import reports that link as an error and
  continues. ``represents`` disables the target permission check, so
  read-only access to the physical table is sufficient.

  Args:
    ctx: the naming.Context holding the naming coordinates for this run.
    manifest: the parsed dbt manifest.json.
    known_ids: set of emitted dbt entry ids.
    linkable_datasets: only nodes whose (database, schema) is in this set get a
      link (the datasets known to live in the import location).

  Returns:
    A list of represents (physical) EntryLink records.
  """
  out: list[EntryLinkRecord] = []
  for uid, node in (manifest.get(_NODES) or {}).items():
    if not _materializes_to_bigquery(node):
      continue
    d_id = naming.entry_id(uid)
    if d_id not in known_ids:
      continue
    database = node.get('database')
    schema = node.get('schema')
    table = node.get('alias') or node.get('name')
    if not (database and schema and table):
      continue
    if (database, schema) not in linkable_datasets:
      continue
    out.append(
        _entry_link(
            ctx,
            'materializes_to',
            ctx.entry_name(d_id),
            _get_bigquery_entry_name(
                ctx.eg_location, database, schema, table
            ),
        )
    )
  return out


def build_entry_links(
    ctx: naming.Context,
    manifest: abc.Mapping[str, Any],
    known_ids: set[str],
    linkable_datasets: set[tuple[str, str]] | None = None,
) -> list[EntryLinkRecord]:
  """Builds all EntryLink records (lineage + semantic edges).

  NOTE: only called when include_entry_links=True.

  Args:
    ctx: the naming.Context holding the naming coordinates for this run.
    manifest: the parsed dbt manifest.json.
    known_ids: the set of Dataplex entry ids the transform emitted; edges that
      reference an id outside this set are dropped.
    linkable_datasets: the BigQuery (database, schema) datasets to emit
      represents (physical) links for -- those known to live in the import
      location (@bigquery entries are named there, as entry links are
      same-region). When None, no physical links are emitted.

  Returns:
    A list of EntryLink records for the resolvable lineage / semantic edges.
  """
  links: list[EntryLinkRecord] = []
  links.extend(_emit_depends_on(ctx, manifest, known_ids))
  links.extend(_emit_consumed_by(ctx, manifest, known_ids))
  links.extend(_emit_defines_semantics_for(ctx, manifest, known_ids))
  links.extend(_emit_derives_from(ctx, manifest, known_ids))
  # TODO(b/546009331): Implement schema-join emission once the backend-side
  # issue is resolved.
  if linkable_datasets is not None:
    links.extend(
        _emit_materializes_to(ctx, manifest, known_ids, linkable_datasets)
    )
  return links
