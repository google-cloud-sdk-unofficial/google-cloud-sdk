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

from collections.abc import Callable, Mapping, Set
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
  ambiguous = set()
  for uid, node in (mapping or {}).items():
    if not predicate(node):
      continue
    name = node.get('name')
    if not name:
      continue
    if name in index:
      # Versioned models share one ``name``, as do same-named models in two
      # packages. Resolving to an arbitrary one would emit a confident link to
      # the wrong entry, so drop the name and emit nothing for it.
      ambiguous.add(name)
      continue
    index[name] = uid
  for name in ambiguous:
    del index[name]
  return index


def _emit_consumed_by(
    ctx: naming.Context, manifest: Mapping[str, Any], known_ids: Set[str]
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
    ctx: naming.Context, manifest: Mapping[str, Any], known_ids: Set[str]
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


def _schema_join_aspect(
    ctx: naming.Context,
    source_sql: str,
    target_sql: str,
    column_pairs: list[tuple[str, str]],
) -> dict[str, Any]:
  """Builds the ``schema-join`` aspect required by schema-join links.

  The ``schema-join`` link type declares ``required_aspects: schema-join``, so
  each link carries a Dataplex-owned ``schema-join`` aspect describing the
  joinable columns (payload follows the aspect type's ``SchemaJoins`` template).

  Args:
    ctx: the naming.Context holding the naming coordinates for this run.
    source_sql: SQL representation (relation name) of the source entity.
    target_sql: SQL representation (relation name) of the target entity.
    column_pairs: (source column, target column) pairs to join on, one per join.

  Returns:
    An aspect map ({aspect_key: {aspectType, data}}) for the link.
  """
  data = {
      'joins': [
          {
              'source': {'name': source_sql, 'fields': [source_field]},
              'target': {'name': target_sql, 'fields': [target_field]},
              # A dbt `relationships` test asserts a user-authored foreign key.
              'type': 'FOREIGN_KEY',
              'inferenceSource': 'USER',
          }
          for source_field, target_field in column_pairs
      ],
      'userManaged': True,
  }
  return {
      ctx.schema_join_key(): {
          'aspectType': ctx.schema_join_fqn(),
          'data': data,
      }
  }


def _emit_schema_join(
    ctx: naming.Context, manifest: Mapping[str, Any], known_ids: Set[str]
) -> list[EntryLinkRecord]:
  """Child model -> parent model, from relationships tests.

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
  nodes = manifest.get(_NODES) or {}
  model_uid_by_name = _index_uid_by_name(
      nodes, lambda n: n.get('resource_type') in _MATERIALIZED_RESOURCE_TYPES
  )
  # unique_id pair -> the columns to join on. The link id is derived from the
  # two endpoints alone, so several relationships tests between the same pair of
  # models have to share one link and one aspect. The pair is ordered so that
  # two tests pointing opposite ways across the same models land on one link
  # rather than two half-populated ones; the join records keep the orientation.
  columns_by_pair: dict[tuple[str, str], list[tuple[str, str]]] = {}
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
    child_col = kwargs.get('column_name')
    parent_col = kwargs.get('field')
    if not child_col or not parent_col:
      continue
    parent_name = naming.parse_ref(kwargs.get('to') or '')
    if not parent_name:
      continue
    parent_uid = model_uid_by_name.get(parent_name)
    if not parent_uid:
      continue
    if (
        naming.entry_id(attached) not in known_ids
        or naming.entry_id(parent_uid) not in known_ids
    ):
      continue
    source_uid, target_uid = sorted((attached, parent_uid))
    if source_uid == attached:
      columns = (child_col, parent_col)
    else:
      columns = (parent_col, child_col)
    pairs = columns_by_pair.setdefault((source_uid, target_uid), [])
    if columns not in pairs:
      pairs.append(columns)

  out: list[EntryLinkRecord] = []
  for (source_uid, target_uid), pairs in columns_by_pair.items():
    source_id = naming.entry_id(source_uid)
    target_id = naming.entry_id(target_uid)
    # The schema-join aspect names the joinable columns; use each model's
    # relation_name (SQL representation), falling back to the entry id.
    source_sql = (nodes.get(source_uid) or {}).get('relation_name') or source_id
    target_sql = (nodes.get(target_uid) or {}).get('relation_name') or target_id
    out.append(
        _entry_link(
            ctx,
            'schema_join',
            ctx.entry_name(source_id),
            ctx.entry_name(target_id),
            aspects=_schema_join_aspect(ctx, source_sql, target_sql, pairs),
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


def materialized_bigquery_projects(manifest: Mapping[str, Any]) -> set[str]:
  """Returns the BigQuery projects (dbt ``database``) of materialized nodes.

  Used to scope the import job's referencedEntryScopes so represents (physical)
  links
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
    linkable_datasets: Set[tuple[str, str]],
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
    manifest: Mapping[str, Any],
    known_ids: Set[str],
    linkable_datasets: Set[tuple[str, str]] | None = None,
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
  links.extend(_emit_schema_join(ctx, manifest, known_ids))
  if linkable_datasets is not None:
    links.extend(
        _emit_materializes_to(ctx, manifest, known_ids, linkable_datasets)
    )
  return links
