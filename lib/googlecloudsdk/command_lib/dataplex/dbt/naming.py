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
"""Resource-name construction for the dbt -> Dataplex transform."""

from __future__ import annotations

import dataclasses

from googlecloudsdk.core import exceptions as core_exceptions


class TransformError(core_exceptions.Error):
  """Raised when dbt artifacts are missing, malformed, or over a size limit.

  Extends core.exceptions.Error so gcloud reports it as a clean `ERROR:`
  message rather than an unexpected-crash traceback. Lives here (not in
  ``transform``) so lower-level modules such as ``entry_builders`` can raise it
  without importing ``transform`` -- which imports them -- and re-exported as
  ``transform.TransformError`` for callers.
  """


# Dataplex caps the length of an entry id; see
# https://cloud.google.com/dataplex/docs/quotas#limits.
MAX_ENTRY_ID_LENGTH = 4000

# Dataplex also caps the size of the metadata an import item carries (same
# quotas page). dbt resources carry arbitrary user content -- compiled SQL,
# macro bodies, wide schemas, free-form `meta` blobs -- so a single aspect or a
# whole entry can outgrow these limits; the transform fails early rather than
# copy the file to GCS and let the import job reject the item server-side.
#
# Max JSON size of a single aspect's `data`. The reserved `schema` /
# data-profile aspects have higher limits, but the dbt connector emits neither
# -- its columns live in a custom `dbt-schema` aspect, which is subject to
# this limit.
MAX_ASPECT_JSON_BYTES = 120 * 1024
# Max total size of one entry (all of its aspects together).
MAX_ENTRY_BYTES = 5 * 1024 * 1024

# Short emitter key -> entryLinkType id. The fully-qualified name is built per
# run against the resolved system-types project via ``Context.link_type_fqn``.
#
# NOTE: ``materializes_to`` is declared here (and therefore advertised by
# ``entry_links.LinkTypeFqns`` for the import job scope) but is not emitted yet.
# Emitting it is deferred because it is a substantial piece of work: a
# materializes-to link targets the physical table's entry in the ``@bigquery``
# system entry group, whose resource name is keyed by the dataset's BigQuery
# REGION -- which the dbt manifest does not carry, so it needs a live `bq`
# lookup per dataset (plus pinning the exact ``@bigquery`` entry-name format).
# The link type stays advertised so the import job scope is ready once emission
# lands. See ``entry_links`` for details.
LINK_TYPE_IDS: dict[str, str] = {
    'depends_on': 'depends-on',
    'materializes_to': 'materializes-to',
    'belongs_to': 'belongs-to',
    'schema_join': 'schema-join',
    'consumed_by': 'consumed-by',
    'defines_semantics_for': 'defines-semantics-for',
    'derives_from': 'derives-from',
}


def entry_id(unique_id: str) -> str:
  """Maps a dbt unique_id to a Dataplex entry id.

  dbt unique_ids look like ``model.my_project.my_model``; Dataplex entry ids
  disallow dots, so they are lowercased and dots become underscores. This is
  lossy (``a.b_c`` and ``a_b.c`` both collapse to ``a_b_c``); callers that build
  many entries should watch for collisions -- see ``entry_builders``.

  Args:
    unique_id: the dbt unique_id (e.g. ``model.my_project.my_model``).

  Returns:
    The Dataplex entry id (lowercased, with dots replaced by underscores).
  """
  return unique_id.lower().replace('.', '_')


@dataclasses.dataclass(frozen=True)
class Context:
  """Holds the naming context for one transform run.

  Three distinct coordinates are involved (the fields cluster into a small
  struct so callers construct them by keyword and can't silently transpose two
  same-typed project strings):

  * The dbt ENTRIES live in the user's own entry group, identified by the
    project NUMBER (``eg_project``) and the entry group's regional location
    (``eg_location``). dbt entry names and entry-link names use these.
  * The dbt aspect / entry types are "connector" 1P types owned by a dedicated
    project per environment (dataplex-connector-types / dataplex-staging-3p-
    types / dataplex-autopush-3p-types) at the `global` location. entryType /
    aspectType references and the aspect map keys use this ``connector_project``
    ID (e.g. `dataplex-staging-3p-types.global.dbt-node`), not a project number.
  * The `contacts` aspect type and the entry link types are CORE 1P types owned
    by a different ``system_project`` (dataplex-types / dataplex-staging-types /
    dataplex-autopush-types), also at `global`.
  """

  eg_project: str
  eg_location: str
  entry_group: str
  connector_project: str
  system_project: str
  types_location: str

  def entry_name(self, resource_entry_id: str) -> str:
    """Returns the full resource name of a dbt entry in the entry group."""
    return 'projects/{0}/locations/{1}/entryGroups/{2}/entries/{3}'.format(
        self.eg_project, self.eg_location, self.entry_group, resource_entry_id
    )

  def entry_type(self, name: str) -> str:
    """Returns the full resource name of a connector-owned entry type."""
    return 'projects/{0}/locations/{1}/entryTypes/{2}'.format(
        self.connector_project, self.types_location, name
    )

  def aspect_fqn(self, name: str) -> str:
    """Returns the full resource name of a connector-owned aspect type."""
    return 'projects/{0}/locations/{1}/aspectTypes/{2}'.format(
        self.connector_project, self.types_location, name
    )

  def aspect_key(self, name: str) -> str:
    """Returns the connector-owned aspect's key for the entry's aspect map."""
    return '{0}.{1}.{2}'.format(
        self.connector_project, self.types_location, name
    )

  def contacts_fqn(self) -> str:
    """Returns the full resource name of the core `contacts` aspect type."""
    return 'projects/{0}/locations/{1}/aspectTypes/contacts'.format(
        self.system_project, self.types_location
    )

  def contacts_key(self) -> str:
    """Returns the `contacts` aspect's key for the entry's aspect map."""
    return '{0}.{1}.contacts'.format(self.system_project, self.types_location)

  def link_type_fqn(self, short_name: str) -> str:
    """Returns the full resource name of a core entry link type."""
    return 'projects/{0}/locations/{1}/entryLinkTypes/{2}'.format(
        self.system_project, self.types_location, LINK_TYPE_IDS[short_name]
    )
