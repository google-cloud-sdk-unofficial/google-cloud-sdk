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

  Two distinct coordinates are involved (the fields cluster into a small
  struct so callers construct them by keyword and can't silently transpose two
  same-typed project strings):

  * The dbt ENTRIES live in the user's own entry group, identified by the
    project NUMBER (``eg_project``) and the entry group's regional location
    (``eg_location``). dbt entry names use these.
  * The dbt aspect / entry types are "connector" 1P types owned by a dedicated
    project per environment (dataplex-connector-types / dataplex-staging-3p-
    types / dataplex-autopush-3p-types) at the `global` location. entryType /
    aspectType references and the aspect map keys use this ``connector_project``
    ID (e.g. `dataplex-staging-3p-types.global.dbt-node`), not a project number.
  """

  eg_project: str
  eg_location: str
  entry_group: str
  connector_project: str
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
