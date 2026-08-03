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
"""Best-effort inference of the BigQuery location from a dbt project.

The BigQuery dataset/table location is a dbt *connection* setting -- it lives in
``profiles.yml`` (``outputs.<target>.location``), NOT in the ``target/``
artifacts (manifest.json / catalog.json). materializes-to links need it to name
the physical @bigquery table entries, so we recover it from the dbt project's
``dbt_project.yml`` (for the profile name), ``profiles.yml`` (for the location),
and ``run_results.json`` (for the *actual* target / profiles dir the run used).
This is best-effort: callers fall back to an explicit ``--bigquery-location``.

Subtleties this module handles:

* The active **target** is not necessarily ``profiles.<profile>.target`` -- a
  run may override it with ``--target`` / ``DBT_TARGET``. The actual value is
  recorded in ``run_results.json`` (``args.target``), which wins when present.
* ``location`` (and ``target``) may be templated with ``{{ env_var(...) }}``;
  those are rendered. Any *other* unresolved Jinja means we can't trust the
  value and report it as un-inferable rather than emit garbage.
* ``location`` is **optional**: when it is absent, dbt-bigquery lets the
  BigQuery client default new datasets to the ``US`` multi-region. We surface
  that as an ``US`` guess tagged ``SOURCE_DEFAULT`` so the caller can warn --
  a pre-existing dataset in another region would make the guess wrong.
"""

from __future__ import annotations

import dataclasses
import json
import os
import re
from typing import Any

from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import encoding
from googlecloudsdk.core.util import files

_DBT_PROJECT_FILE = 'dbt_project.yml'
_PROFILES_FILE = 'profiles.yml'
_RUN_RESULTS_FILE = 'run_results.json'
_DBT_PROFILES_DIR_ENV = 'DBT_PROFILES_DIR'

# dbt-bigquery leaves ``location`` optional; when it is unset the underlying
# BigQuery client creates new datasets in the ``US`` multi-region.
_BIGQUERY_DEFAULT_LOCATION = 'us'

# Where an inferred location came from -- lets callers phrase the right message.
SOURCE_PROFILES = 'profiles'  # read from outputs.<target>.location.
SOURCE_DEFAULT = 'default'  # assumed US because profiles.yml sets none.

# Matches ``{{ env_var('NAME') }}`` and ``{{ env_var('NAME', 'default') }}``
# (single or double quotes, arbitrary surrounding whitespace).
_ENV_VAR_RE = re.compile(
    r"""\{\{\s*env_var\(\s*['"]([^'"]+)['"]\s*"""
    r"""(?:,\s*['"]([^'"]*)['"]\s*)?\)\s*\}\}"""
)


@dataclasses.dataclass(frozen=True)
class InferredLocation:
  """A best-effort BigQuery location and where it was inferred from.

  Attributes:
    location: the Dataplex region, lower-cased (e.g. 'eu', 'us', 'us-central1').
    source: ``SOURCE_PROFILES`` when read from ``outputs.<target>.location``, or
      ``SOURCE_DEFAULT`` when assumed to be the ``US`` multi-region because the
      profile sets no location.
  """

  location: str
  source: str


def _load_yaml(path: str) -> Any:
  """Loads a YAML file, returning None if it is absent or unparseable."""
  if not os.path.isfile(path):
    return None
  try:
    return yaml.load_path(path)
  except yaml.Error:
    return None


def _load_json(path: str) -> Any:
  """Loads a JSON file, returning None if it is absent or unparseable."""
  if not os.path.isfile(path):
    return None
  try:
    return json.loads(files.ReadFileContents(path))
  except (ValueError, files.Error):
    return None


def _render_templated(value: str) -> str | None:
  """Resolves ``{{ env_var(...) }}`` refs in a scalar dbt config value.

  Args:
    value: the raw scalar from profiles.yml.

  Returns:
    The rendered string, or None if the value carries Jinja we could not fully
    resolve (an unset ``env_var`` with no default, or any other expression) --
    in which case the caller must not trust it.
  """
  if not isinstance(value, str) or '{{' not in value:
    return value
  unresolved = False

  def _sub(match: re.Match[str]) -> str:
    nonlocal unresolved
    name, default = match.group(1), match.group(2)
    env = encoding.GetEncodedValue(os.environ, name)
    if env is not None:
      return env
    if default is not None:
      return default
    unresolved = True
    return ''

  rendered = _ENV_VAR_RE.sub(_sub, value)
  if unresolved or '{{' in rendered:
    return None
  return rendered


def _project_root(artifacts_path: str) -> str:
  """Returns the dbt project root for an artifacts path.

  ``artifacts_path`` may point at the project root or directly at its
  ``target/`` subdir; ``dbt_project.yml`` lives in the project root, so also
  check the parent.

  Args:
    artifacts_path: the value passed as --artifacts-path.

  Returns:
    The directory to look for dbt_project.yml / profiles.yml in.
  """
  if os.path.isfile(os.path.join(artifacts_path, _DBT_PROJECT_FILE)):
    return artifacts_path
  parent = os.path.dirname(os.path.abspath(artifacts_path))
  if os.path.isfile(os.path.join(parent, _DBT_PROJECT_FILE)):
    return parent
  return artifacts_path


def _run_results_args(artifacts_path: str) -> dict[str, Any]:
  """Returns the ``args`` block of run_results.json, or {} if unavailable.

  run_results.json lives in the dbt ``target/`` dir; --artifacts-path may point
  at the project root or at ``target/`` directly, so check both.

  Args:
    artifacts_path: the --artifacts-path value.

  Returns:
    The recorded invocation args (includes the actual ``target`` and
    ``profiles_dir`` the run used), or an empty dict.
  """
  for base in (artifacts_path, os.path.join(artifacts_path, 'target')):
    data = _load_json(os.path.join(base, _RUN_RESULTS_FILE))
    if isinstance(data, dict) and isinstance(data.get('args'), dict):
      return data['args']
  return {}


def _profiles_search_dirs(
    project_root: str, profiles_dir_override: str | None
) -> list[str]:
  """Directories to look for profiles.yml, in dbt's precedence order."""
  dirs = []
  # The profiles dir the run actually used (recorded in run_results.json) is the
  # most authoritative -- it reflects --profiles-dir / DBT_PROFILES_DIR / cwd as
  # resolved at run time.
  if profiles_dir_override:
    dirs.append(os.path.expanduser(profiles_dir_override))
  env_dir = encoding.GetEncodedValue(os.environ, _DBT_PROFILES_DIR_ENV)
  if env_dir:
    dirs.append(env_dir)
  dirs.append(project_root)
  dirs.append(os.path.join(os.path.expanduser('~'), '.dbt'))
  return dirs


def _select_output(
    profile: dict[str, Any], target_override: str | None
) -> dict[str, Any] | None:
  """Returns the active output block of a dbt profile, or None.

  Args:
    profile: the profile block from profiles.yml.
    target_override: the actual target from run_results.json, if known; wins
      over the profile's declared default ``target``.

  Returns:
    The chosen output block, or None.
  """
  outputs = profile.get('outputs')
  if not isinstance(outputs, dict) or not outputs:
    return None
  target = target_override or profile.get('target')
  if isinstance(target, str):
    target = _render_templated(target)
  output = outputs.get(target) if target else None
  if not isinstance(output, dict) and len(outputs) == 1:
    # No (or unresolved) target, but a single output -- use it.
    output = next(iter(outputs.values()))
  return output if isinstance(output, dict) else None


def infer_bigquery_location(
    artifacts_path: str,
) -> InferredLocation | None:
  """Best-effort BigQuery location for the dbt project, or None.

  Reads the dbt project's ``profiles.yml`` (via the profile named in
  ``dbt_project.yml``, or the sole profile) and returns
  ``outputs.<target>.location`` -- with the target taken from
  ``run_results.json`` when available. When the profile sets no location for a
  BigQuery output, returns the ``US`` multi-region tagged ``SOURCE_DEFAULT``
  (dbt-bigquery's default for new datasets). Returns None when nothing usable
  can be determined -- the caller then asks for an explicit --bigquery-location.

  Args:
    artifacts_path: the --artifacts-path value (project root or target/ dir).

  Returns:
    An ``InferredLocation`` (location lower-cased), or None.
  """
  root = _project_root(artifacts_path)
  rr_args = _run_results_args(artifacts_path)
  target_override = rr_args.get('target')
  profiles_dir_override = rr_args.get('profiles_dir')

  project_yml = _load_yaml(os.path.join(root, _DBT_PROJECT_FILE))
  profile_name = (
      project_yml.get('profile') if isinstance(project_yml, dict) else None
  )

  profiles = None
  for profiles_dir in _profiles_search_dirs(root, profiles_dir_override):
    profiles = _load_yaml(os.path.join(profiles_dir, _PROFILES_FILE))
    if isinstance(profiles, dict):
      break
  if not isinstance(profiles, dict):
    return None

  profile = None
  if profile_name and isinstance(profiles.get(profile_name), dict):
    profile = profiles[profile_name]
  elif len(profiles) == 1 and isinstance(next(iter(profiles.values())), dict):
    profile = next(iter(profiles.values()))
  if profile is None:
    return None

  output = _select_output(profile, target_override)
  if not output:
    return None

  location = output.get('location')
  if isinstance(location, str) and location.strip():
    rendered = _render_templated(location.strip())
    if rendered and rendered.strip():
      return InferredLocation(rendered.strip().lower(), SOURCE_PROFILES)
    # The profile set a location we couldn't resolve (e.g. an unset env_var).
    # Don't guess US -- it may well be elsewhere; let the caller ask.
    return None

  # No location set. dbt-bigquery defaults new datasets to the US multi-region;
  # only assume that for a BigQuery output (dbt requires ``type``, but tolerate
  # it being absent for this dbt-only command).
  if output.get('type') in (None, 'bigquery'):
    return InferredLocation(_BIGQUERY_DEFAULT_LOCATION, SOURCE_DEFAULT)
  return None
