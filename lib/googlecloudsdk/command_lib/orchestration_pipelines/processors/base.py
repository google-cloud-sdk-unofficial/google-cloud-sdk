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
"""Base action processor for Orchestration Pipelines."""

from collections.abc import MutableMapping, Sequence
import hashlib
import pathlib
from typing import Any

from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.orchestration_pipelines.tools import python_environment
from googlecloudsdk.core import log


class ActionProcessor:
  """Base class for engine-specific action processors."""

  LIBS_EXTRACT_DIR = "libs"

  def __init__(
      self,
      action: MutableMapping[str, Any],
      work_dir: pathlib.Path,
      artifact_base_uri: str,
      subprocess_mod: Any,
      defaults: MutableMapping[str, Any],
      requirements_path: pathlib.Path | None = None,
  ):
    self.action = action
    self._work_dir = work_dir
    self._artifact_base_uri = artifact_base_uri
    self._env_pack_file = None
    self._subprocess_mod = subprocess_mod
    self._defaults = defaults
    self.full_python_path = None
    self.requirements_path = requirements_path

  def process_action(self):
    """Processes a single action in the pipeline, resolving local paths to GCS URIs."""

    log.debug(f"Processing action: {self.action.get('name')}")

    if self._has_valid_requirements():
      python_version = self._get_python_version()
      if python_version:
        self.full_python_path = f"./{self.LIBS_EXTRACT_DIR}/lib/python{python_version}/site-packages"

        with self.requirements_path.open("rb") as f:
          reqs_hash = hashlib.md5(f.read()).hexdigest()
        self._env_pack_file = (
            f"environment-{reqs_hash}-python{python_version}.tar.gz"
        )
        log.debug(f"Resolved environment pack file: {self._env_pack_file}")

        env_pack_path = self._work_dir / self._env_pack_file
        if not env_pack_path.exists():
          log.debug(f"Creating environment pack at {env_pack_path}...")
          python_environment.build_env_local(
              self._subprocess_mod,
              self._work_dir,
              self.requirements_path,
              env_pack_path,
              python_version,
          )

        if not env_pack_path.exists():
          raise exceptions.BadFileException(
              f"Failed to create environment file: {env_pack_path}"
          )

        # Add to archives
        env_pack_uri = f"{self._artifact_base_uri}{self._env_pack_file}#{self.LIBS_EXTRACT_DIR}"
        self.action.setdefault("archiveUris", [])
        if not any(env_pack_uri in arch for arch in self.action["archiveUris"]):
          self.action["archiveUris"].append(env_pack_uri)

    self._resolve_main_file_path()
    self._resolve_py_files()

    self._update_yaml_properties(self.action)

  @property
  def env_pack_file(self) -> str | None:
    """Returns the name of the generated environment pack file."""
    return self._env_pack_file

  def _resolve_main_file_path(self) -> bool:
    """Checks for presence of and resolves mainFilePath to GCS URI.

    Returns:
      True if mainFilePath is present in action, False otherwise.
    """
    if "mainFilePath" not in self.action:
      return False

    raw_path = self.action["mainFilePath"]
    if not isinstance(raw_path, str):
      raise exceptions.BadFileException(
          "The value of 'mainFilePath' in the action must be a string, found"
          f" type {type(raw_path).__name__}: {raw_path}"
      )

    if raw_path.startswith("gs://"):
      return True

    local_path = pathlib.Path(raw_path.lstrip("/"))

    absolute_local_path = self._work_dir / local_path
    if not absolute_local_path.exists():
      raise exceptions.BadFileException(
          f"File in YAML does not exist locally: {local_path}"
      )

    self.action["mainFilePath"] = (
        f"{self._artifact_base_uri}{local_path.as_posix()}"
    )
    return True

  def _resolve_py_files(self) -> bool:
    """Checks for presence of and resolves pyFiles to GCS URIs.

    Returns:
      True if pyFiles is present in action, False otherwise.
    """
    py_files = self.action.get("pyFiles")
    if py_files is None:
      return False

    if not isinstance(py_files, list):
      raise exceptions.BadFileException(
          "The value of 'pyFiles' in the action must be a list, found type "
          f"{type(py_files).__name__}: {py_files}"
      )

    resolved_py_files = []
    for raw_path in py_files:
      if raw_path.startswith("gs://"):
        resolved_py_files.append(raw_path)
        continue

      local_path = pathlib.Path(raw_path.lstrip("/"))
      absolute_local_path = self._work_dir / local_path

      if not absolute_local_path.exists():
        raise exceptions.BadFileException(
            f"File in YAML does not exist locally: {local_path}"
        )

      resolved_py_files.append(
          f"{self._artifact_base_uri}{local_path.as_posix()}"
      )

    self.action["pyFiles"] = resolved_py_files
    return True

  def _get_python_version(self) -> str | None:
    """Returns the Python version for this action, or None if not specified."""
    return None

  def _update_yaml_properties(self, action):
    """Performs updates on YAML properties."""
    pass

  def _has_valid_requirements(self) -> bool:
    """Checks if requirements file exists and has at least one non-comment line."""
    if not self.requirements_path or not self.requirements_path.exists():
      return False

    with self.requirements_path.open("r") as f:
      for line in f:
        line = line.strip()
        if line and not line.startswith("#"):
          return True
    return False

  @staticmethod
  def _get_nested_dict(
      d: MutableMapping[str, Any], keys: Sequence[str]
  ) -> MutableMapping[str, Any]:
    """Gets a nested dictionary from `d`.

    Creates keys with empty dictionaries if they don't exist.

    Args:
      d: The dictionary to traverse.
      keys: A sequence of keys to follow to reach the nested dictionary.
    """
    current = d
    for key in keys:
      current = current.setdefault(key, {})
    return current
