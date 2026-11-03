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
"""Packages a dbt project and its generated `profiles.yml` into one `.tar.gz`.

The archive `dbt_<action>.tar.gz` holds the allow-listed project files plus the
generated `profiles.yml` under a top-level `dbt/`
directory, next to `dbt_project.yml`, where dbt finds it when it runs from the
project directory. It is built deterministically (sorted entries, fixed
metadata, gzip without timestamp) so packaging an unchanged project yields the
same bytes and SHA-256, which lets the uploader skip objects that already exist.
"""

from collections.abc import Mapping, Sequence
import gzip
import hashlib
import os
import pathlib
import re
import shutil
import subprocess
import tarfile
from typing import Any

import frozendict
from googlecloudsdk.command_lib.orchestration_pipelines.serverless_orchestration import errors
from googlecloudsdk.command_lib.orchestration_pipelines.serverless_orchestration import pipeline_loader
from googlecloudsdk.command_lib.orchestration_pipelines.serverless_orchestration.packagers import models
from googlecloudsdk.core import log
from googlecloudsdk.core import yaml

ARCHIVE_NAME = "dbt_{action}.tar.gz"
ARCHIVE_ROOT_DIR = "dbt"
# Path of the generated profile inside the project directory; the compiler
# passes `--profiles-dir .` so dbt reads it from the project directory.
PROFILES_ARCHIVE_PATH = "profiles.yml"
DBT_PROJECT_FILE = "dbt_project.yml"
# Project files and directories bundled into the archive (DBT design doc). The
# user's own `profiles.yml`, `target/`, `logs/` and `.venv/` are never bundled.
INCLUDED_FILES = (
    DBT_PROJECT_FILE,
    "packages.yml",
    "dependencies.yml",
    "package-lock.yml",
    "selectors.yml",
)
INCLUDED_DIRS = (
    "analyses",
    "dbt_packages",
    "macros",
    "models",
    "seeds",
    "snapshots",
    "tests",
)
# `dbt deps` vendors packages into `dbt_packages/` when one of these exists.
_PACKAGE_FILES = ("packages.yml", "dependencies.yml")
_EXCLUDED_DIR_NAMES = frozenset({"__pycache__"})
_EXCLUDED_SUFFIXES = frozenset({".pyc"})

# Fixed entry metadata so the archive bytes only depend on the file contents.
_TAR_MTIME = 1767225600  # 2026-01-01T00:00:00Z
_TAR_FILE_MODE = 0o644
_TAR_DIR_MODE = 0o755
_HASH_CHUNK_SIZE = 1024 * 1024
_DBT_DEPS_TIMEOUT_SECONDS = 300

# `dbt_project.yml` files may contain Jinja expressions (`{{ ... }}`,
# `{% ... %}`, or `{# ... #}`) in fields such as `vars` or hooks, which are not
# valid raw YAML.
_JINJA_MASK = "__DBT_JINJA_TEMPLATE__"
_JINJA_BLOCK_RE = re.compile(r"\{\{.*?\}\}|\{%.*?%\}|\{#.*?#\}")
_JINJA_DELIMITERS = ("{{", "}}", "{%", "%}", "{#", "#}")

# `profileConfig` keys copied into `profiles.yml`; dbt-bigquery rejects any
# other key.
_PROFILE_KEYS = (
    "project",
    "dataset",
    "location",
    "threads",
    "priority",
    "job_execution_timeout_seconds",
    "job_retries",
    "maximum_bytes_billed",
    "gcs_bucket",
    "compute_region",
)
_REQUIRED_PROFILE_KEYS = ("project", "dataset")
_STRING_PROFILE_KEYS = frozenset({
    "project",
    "dataset",
    "location",
    "priority",
    "gcs_bucket",
    "compute_region",
})
_POSITIVE_INT_PROFILE_KEYS = frozenset({
    "threads",
    "job_execution_timeout_seconds",
    "maximum_bytes_billed",
})
_NON_NEGATIVE_INT_PROFILE_KEYS = frozenset({"job_retries"})
# DCS defaults (DBT design doc) applied when the key is not set.
_PROFILE_DEFAULTS = frozendict.frozendict(
    {"threads": 4, "job_execution_timeout_seconds": 900}
)
# Inline credentials are never written: the runtime service account is used.
_BLOCKED_PROFILE_KEYS = frozenset({
    "keyfile",
    "keyfile_json",
    "token",
    "refresh_token",
    "client_id",
    "client_secret",
    "token_uri",
})


def ExtractProfileName(action: pipeline_loader.DbtAction) -> str:
  """Extracts and validates the `profile` name from `dbt_project.yml`.

  Args:
    action: The dbt action whose project directory is inspected.

  Returns:
    The top-level profile name declared in `dbt_project.yml`.

  Raises:
    errors.PackagingError: If the project directory or `dbt_project.yml` is
      missing, a symbolic link, invalid YAML, or does not set a valid literal
      `profile` string.
  """
  dbt_project_file = _ResolveDbtProjectFile(action)
  parsed = _LoadMaskedDbtProjectYaml(action.name, dbt_project_file)
  profile = _RequireNonEmptyUnpaddedStr(
      parsed.get("profile"),
      label=f"`profile` in '{dbt_project_file}'",
      action_name=action.name,
  )
  if _JINJA_MASK in profile:
    raise errors.PackagingError(
        f"Action '{action.name}': `profile` in '{dbt_project_file}' must be a"
        " literal string, not a Jinja template."
    )
  return profile


def GenerateProfilesYaml(
    action: pipeline_loader.DbtAction,
    target: str,
    profile_name: str | None = None,
) -> str:
  """Renders the `profiles.yml` for one dbt action and target.

  The top-level profile key is read from the `profile` field of the project's
  `dbt_project.yml` (unless already extracted and passed via `profile_name`).
  The profile is always `type: bigquery` with `method: oauth`, so the run uses
  the runtime service account and no credentials are packaged.

  Args:
    action: The dbt action whose `profile_config` is rendered.
    target: The dbt target name (the deployment environment).
    profile_name: Optional pre-extracted `profile` key from `dbt_project.yml`.
      When None, extracted from `action.project_directory / "dbt_project.yml"`.

  Returns:
    The `profiles.yml` document as a string.

  Raises:
    errors.PackagingError: If `dbt_project.yml`, `profile_config`, `target`, or
      `profile_name` is invalid.
  """
  _RequireNonEmptyUnpaddedStr(
      target, label="`target`", action_name=action.name
  )
  if profile_name is None:
    profile_name = ExtractProfileName(action)
  else:
    _RequireNonEmptyUnpaddedStr(
        profile_name, label="`profile_name`", action_name=action.name
    )
  output = _BuildBigQueryTargetOutputFromAction(action)
  return yaml.dump(
      {
          profile_name: {
              "target": target,
              "outputs": {target: output},
          }
      }
  )


class DbtPackager:
  """Packages a dbt project directory into a single deterministic archive."""

  def Package(
      self,
      action: pipeline_loader.DbtAction,
      context: models.PackagingContext,
  ) -> models.PackagedArtifact:
    """Bundles the allow-listed project files and `profiles.yml` into a tar.gz.

    Args:
      action: The dbt action to package.
      context: The per-deployment packaging context.

    Returns:
      The packaged artifact containing the single `.tar.gz` staged under
      `context.staging_dir`.

    Raises:
      errors.PackagingError: If the project is invalid or cannot be archived.
    """
    if (
        not isinstance(action.name, str)
        or not action.name.strip()
        or action.name in {".", ".."}
        or "/" in action.name
        or "\\" in action.name
    ):
      raise errors.PackagingError(
          f"Invalid dbt action name '{action.name}': must be a non-empty"
          " single path segment."
      )
    project_dir = action.project_directory
    profile_name = ExtractProfileName(action)
    profiles_yaml = GenerateProfilesYaml(
        action, context.target, profile_name=profile_name
    )
    archive_name = ARCHIVE_NAME.format(action=action.name)
    archive_path = context.staging_dir / archive_name
    profiles_path = _WriteStagedProfilesYaml(
        context.staging_dir / action.name,
        profiles_yaml,
        project_dir,
        archive_path,
    )
    _VendorPackages(project_dir, profiles_path.parent, profile_name)
    sha256 = _CreateProjectArchive(project_dir, profiles_path, archive_path)
    return models.PackagedArtifact(
        action_name=action.name,
        files=(
            models.StagedFile(
                local_path=archive_path,
                relative_path=archive_name,
                sha256=sha256,
            ),
        ),
    )


def _ResolveDbtProjectFile(
    action: pipeline_loader.DbtAction,
) -> pathlib.Path:
  """Validates the project directory and returns the `dbt_project.yml` path."""
  project_dir = action.project_directory
  if project_dir.is_symlink():
    raise errors.PackagingError(
        f"Action '{action.name}': dbt project directory '{project_dir}' must"
        " not be a symbolic link."
    )
  dbt_project_file = project_dir / DBT_PROJECT_FILE
  if dbt_project_file.is_symlink():
    raise errors.PackagingError(
        f"Action '{action.name}': '{dbt_project_file}' must not be a"
        " symbolic link."
    )
  if not dbt_project_file.is_file():
    alt_file = project_dir / "dbt_project.yaml"
    if alt_file.is_file() or alt_file.is_symlink():
      raise errors.PackagingError(
          f"Action '{action.name}': found '{alt_file}', but dbt requires"
          f" `{DBT_PROJECT_FILE}`."
      )
    raise errors.PackagingError(
        f"Action '{action.name}': '{project_dir}' is not a dbt project"
        f" (no `{DBT_PROJECT_FILE}`)."
    )
  return dbt_project_file


def _LoadMaskedDbtProjectYaml(
    action_name: str, path: pathlib.Path
) -> Mapping[str, Any]:
  """Loads `dbt_project.yml` with Jinja expressions masked out."""
  try:
    content = path.read_text(encoding="utf-8")
    masked_content = _JINJA_BLOCK_RE.sub(_JINJA_MASK, content)
    for delimiter in _JINJA_DELIMITERS:
      masked_content = masked_content.replace(delimiter, _JINJA_MASK)
    parsed = yaml.load(masked_content)
  except (OSError, UnicodeDecodeError, yaml.Error) as e:
    raise errors.PackagingError(
        f"Action '{action_name}': failed to parse '{path}': {e}"
    ) from e
  if not isinstance(parsed, Mapping):
    raise errors.PackagingError(
        f"Action '{action_name}': expected a YAML mapping in '{path}'."
    )
  return parsed


def _RequireNonEmptyUnpaddedStr(
    value: Any, *, label: str, action_name: str
) -> str:
  """Validates that `value` is a non-empty string without outer whitespace."""
  if not isinstance(value, str) or not value.strip():
    raise errors.PackagingError(
        f"Action '{action_name}': {label} must be a non-empty string."
    )
  if value != value.strip():
    raise errors.PackagingError(
        f"Action '{action_name}': {label} must not have leading or trailing"
        " whitespace."
    )
  return value


def _BuildBigQueryTargetOutputFromAction(
    action: pipeline_loader.DbtAction,
) -> dict[str, Any]:
  """Builds the validated BigQuery target output mapping for `profiles.yml`."""
  _VerifyProfileConfig(action.name, action.profile_config)
  output: dict[str, Any] = {"type": "bigquery", "method": "oauth"}
  for key, value in action.profile_config.items():
    if key in ("type", "method"):
      continue
    if value is None and key not in _REQUIRED_PROFILE_KEYS:
      continue
    output[key] = value
  for key, default in _PROFILE_DEFAULTS.items():
    output.setdefault(key, default)
  return output


def _VerifyProfileConfig(action_name: str, profile_config: Any) -> None:
  """Verifies that `profile_config` is a valid mapping with required keys."""
  owner = f"Action '{action_name}': `profileConfig`"
  if not isinstance(profile_config, Mapping):
    raise errors.PackagingError(f"{owner} must be a mapping.")
  for key, value in profile_config.items():
    _VerifyProfileConfigEntry(action_name, key, value)
  for key in _REQUIRED_PROFILE_KEYS:
    if profile_config.get(key) is None:
      raise errors.PackagingError(f"{owner} must set `{key}`.")


def _VerifyProfileConfigEntry(
    action_name: str, key: Any, value: Any
) -> None:
  """Verifies a single key-value entry in `profileConfig`."""
  owner = f"Action '{action_name}': `profileConfig`"
  if not isinstance(key, str):
    raise errors.PackagingError(
        f"{owner}: unsupported key `{key}`. Supported keys:"
        f" {', '.join(_PROFILE_KEYS)}."
    )
  if key in _BLOCKED_PROFILE_KEYS:
    raise errors.PackagingError(
        f"{owner} must not contain credentials (`{key}`); dbt runs with"
        " the pipeline's service account."
    )
  if key in ("type", "method"):
    expected = "bigquery" if key == "type" else "oauth"
    if value != expected:
      raise errors.PackagingError(
          f"{owner}: `{key}` must be `{expected}`, got `{value}`."
      )
    return
  if key not in _PROFILE_KEYS:
    raise errors.PackagingError(
        f"{owner}: unsupported key `{key}`. Supported keys:"
        f" {', '.join(_PROFILE_KEYS)}."
    )
  if value is not None:
    _ValidateProfileValue(action_name, key, value)


def _ValidateProfileValue(action_name: str, key: str, value: Any) -> None:
  """Validates a single `profileConfig` entry value.

  Args:
    action_name: Name of the dbt action being validated.
    key: Canonical key name in `profileConfig`.
    value: Value associated with `key`.

  Raises:
    errors.PackagingError: If `value` has an invalid type or value for `key`.
  """
  owner = f"Action '{action_name}': `profileConfig`"
  if key in _STRING_PROFILE_KEYS:
    _RequireNonEmptyUnpaddedStr(
        value, label=f"`profileConfig`: `{key}`", action_name=action_name
    )
  elif key in _POSITIVE_INT_PROFILE_KEYS:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
      raise errors.PackagingError(
          f"{owner}: `{key}` must be a positive integer, got `{value}`."
      )
  elif key in _NON_NEGATIVE_INT_PROFILE_KEYS:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
      raise errors.PackagingError(
          f"{owner}: `{key}` must be a non-negative integer, got `{value}`."
      )


def _WriteStagedProfilesYaml(
    action_dir: pathlib.Path,
    profiles_yaml: str,
    project_dir: pathlib.Path,
    archive_path: pathlib.Path,
) -> pathlib.Path:
  """Writes the generated `profiles.yml` into the action staging directory."""
  profiles_path = action_dir / PROFILES_ARCHIVE_PATH
  try:
    profiles_path.parent.mkdir(parents=True, exist_ok=True)
    # Bytes, so the archive bytes (and SHA-256) do not depend on the
    # platform's line endings.
    profiles_path.write_bytes(profiles_yaml.encode("utf-8"))
  except OSError as e:
    raise errors.PackagingError(
        f"Failed to package '{project_dir}' into '{archive_path}': {e}"
    ) from e
  return profiles_path


def _VendorPackages(
    project_dir: pathlib.Path, profiles_dir: pathlib.Path, profile_name: str
) -> None:
  """Runs `dbt deps` so `dbt_packages/` ships inside the archive.

  Only runs when the project declares packages (`packages.yml` or
  `dependencies.yml`), so projects without packages do not need dbt installed.

  Args:
    project_dir: The dbt project directory.
    profiles_dir: Directory holding the generated `profiles.yml`.
    profile_name: Top-level key of the generated `profiles.yml`.

  Raises:
    errors.PackagingError: If dbt is not installed or `dbt deps` fails.
  """
  if not any(
      not (project_dir / name).is_symlink() and (project_dir / name).is_file()
      for name in _PACKAGE_FILES
  ):
    return
  dbt_executable = _ResolveDbtExecutable(project_dir)
  if dbt_executable is None:
    raise errors.PackagingError(
        f"'{project_dir}' declares dbt packages, but no `dbt` executable was"
        " found in its `.venv/bin` or on PATH; install dbt to vendor them."
    )
  command = [
      dbt_executable,
      "deps",
      "--project-dir",
      str(project_dir),
      "--profiles-dir",
      str(profiles_dir),
      "--profile",
      profile_name,
  ]
  log.status.Print("Running `dbt deps`...")
  try:
    subprocess.run(
        command,
        cwd=str(project_dir),
        check=True,
        capture_output=True,
        text=True,
        timeout=_DBT_DEPS_TIMEOUT_SECONDS,
    )
  except subprocess.TimeoutExpired as e:
    raise errors.PackagingError(
        f"`dbt deps` timed out after {e.timeout}s in '{project_dir}'."
    ) from e
  except (subprocess.SubprocessError, OSError) as e:
    stderr = ""
    stdout = ""
    if isinstance(e, subprocess.CalledProcessError):
      stderr = (e.stderr or "").strip()
      stdout = (e.stdout or "").strip()
    details = stderr or stdout or str(e).strip()
    raise errors.PackagingError(
        f"`dbt deps` failed in '{project_dir}': {details}"
    ) from e


def _ResolveDbtExecutable(project_dir: pathlib.Path) -> str | None:
  """Resolves the dbt executable from the project `.venv` or `PATH`.

  Args:
    project_dir: The dbt project directory.

  Returns:
    Path to the `dbt` executable, or None if no executable `dbt` binary is found
    in `.venv/bin/dbt` or on `PATH`.
  """
  venv_dbt = project_dir / ".venv" / "bin" / "dbt"
  if (
      not venv_dbt.is_symlink()
      and venv_dbt.is_file()
      and os.access(venv_dbt, os.X_OK)
  ):
    return str(venv_dbt)
  return shutil.which("dbt")


def _CreateProjectArchive(
    project_dir: pathlib.Path,
    profiles_path: pathlib.Path,
    archive_path: pathlib.Path,
) -> str:
  """Bundles `project_dir` and `profiles_path` into `archive_path`.

  Args:
    project_dir: The dbt project directory.
    profiles_path: Path to the staged `profiles.yml` file.
    archive_path: Destination `.tar.gz` archive path.

  Returns:
    The hex SHA-256 digest of the created archive.

  Raises:
    errors.PackagingError: If reading project files or writing the archive
      fails.
  """
  try:
    project_paths = _CollectProjectPaths(project_dir)
    _WriteDeterministicTarGzArchive(
        project_dir, project_paths, profiles_path, archive_path
    )
    sha256 = _Sha256(archive_path)
  except (OSError, tarfile.TarError) as e:
    raise errors.PackagingError(
        f"Failed to package '{project_dir}' into '{archive_path}': {e}"
    ) from e
  log.info(
      "Packaged %d project paths of '%s' into '%s' (sha256 %s).",
      len(project_paths),
      project_dir,
      archive_path,
      sha256,
  )
  return sha256


def _CollectProjectPaths(project_dir: pathlib.Path) -> list[pathlib.Path]:
  """Returns the allow-listed project paths, relative to `project_dir`.

  Symbolic links are skipped: the runtime rejects them when extracting.

  Args:
    project_dir: The dbt project directory.

  Returns:
    Sorted relative paths of allow-listed files and directories under
    `project_dir`.
  """
  collected: set[pathlib.Path] = set()
  for name in INCLUDED_FILES:
    candidate = project_dir / name
    if not candidate.is_symlink() and candidate.is_file():
      collected.add(pathlib.Path(name))
  for name in INCLUDED_DIRS:
    root = project_dir / name
    if root.is_symlink() or not root.is_dir():
      continue
    collected.add(pathlib.Path(name))
    for child in root.rglob("*"):
      relative = child.relative_to(project_dir)
      if (
          child.is_symlink()
          or _IsExcluded(relative)
          or _HasSymlinkAncestor(project_dir, relative)
      ):
        continue
      if child.is_file() or child.is_dir():
        collected.add(relative)
  return sorted(collected, key=lambda path: path.as_posix())


def _IsExcluded(relative_path: pathlib.Path) -> bool:
  """Returns True if `relative_path` should be excluded from the archive."""
  return (
      not _EXCLUDED_DIR_NAMES.isdisjoint(relative_path.parts)
      or relative_path.suffix in _EXCLUDED_SUFFIXES
  )


def _HasSymlinkAncestor(
    project_dir: pathlib.Path, relative_path: pathlib.Path
) -> bool:
  """Returns True if any parent directory of `relative_path` is a symlink."""
  return any(
      (project_dir / parent).is_symlink()
      for parent in relative_path.parents
      if parent != pathlib.Path(".")
  )


def _WriteDeterministicTarGzArchive(
    project_dir: pathlib.Path,
    project_paths: Sequence[pathlib.Path],
    profiles_path: pathlib.Path,
    archive_path: pathlib.Path,
) -> None:
  """Writes a reproducible `.tar.gz` archive of the project and profile."""
  with (
      archive_path.open("wb") as raw_stream,
      gzip.GzipFile(
          filename="", mode="wb", fileobj=raw_stream, mtime=0
      ) as gzip_stream,
      tarfile.open(fileobj=gzip_stream, mode="w") as tar,
  ):
    tar.add(
        str(project_dir),
        arcname=ARCHIVE_ROOT_DIR,
        recursive=False,
        filter=_NormalizeTarInfo,
    )
    for relative in project_paths:
      tar.add(
          str(project_dir / relative),
          arcname=f"{ARCHIVE_ROOT_DIR}/{relative.as_posix()}",
          recursive=False,
          filter=_NormalizeTarInfo,
      )
    tar.add(
        str(profiles_path),
        arcname=f"{ARCHIVE_ROOT_DIR}/{PROFILES_ARCHIVE_PATH}",
        filter=_NormalizeTarInfo,
    )


def _NormalizeTarInfo(tarinfo: tarfile.TarInfo) -> tarfile.TarInfo:
  """Fixes the entry metadata so the archive is reproducible."""
  tarinfo.mtime = _TAR_MTIME
  tarinfo.uid = 0
  tarinfo.gid = 0
  tarinfo.uname = ""
  tarinfo.gname = ""
  tarinfo.mode = _TAR_DIR_MODE if tarinfo.isdir() else _TAR_FILE_MODE
  return tarinfo


def _Sha256(path: pathlib.Path) -> str:
  """Returns the hex SHA-256 digest of a file."""
  digest = hashlib.sha256()
  with path.open("rb") as stream:
    for chunk in iter(lambda: stream.read(_HASH_CHUNK_SIZE), b""):
      digest.update(chunk)
  return digest.hexdigest()
