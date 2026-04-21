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
"""Generates sync rules from Dockerfile instructions."""

import dataclasses
import json
import os
import posixpath
import shlex
from typing import Sequence

from googlecloudsdk.command_lib.run.sync import dockerfile_parser
from googlecloudsdk.core import log

_DOCKERFILE_NAME = 'Dockerfile'


@dataclasses.dataclass(frozen=True)
class SyncRule:
  """Sync rule for a file or folder.

  Each sync rule contains src and dest.
  - Src is relative to source directory on developer machine.
  - Dest is absolute path to the destination in the container.
  """

  src: str
  dest: str


def _CheckAndUpdateWorkdir(line: str, current_workdir: str) -> str:
  """Checks if the line is a WORKDIR instruction and returns the workdir."""
  parts = line.split(None, 1)
  if len(parts) == 2:
    if parts[0].upper() == 'WORKDIR':
      new_workdir = parts[1].strip()

      if posixpath.isabs(new_workdir):
        return new_workdir
      else:
        return posixpath.join(current_workdir, new_workdir)

  return current_workdir


def _GetSrcDestJsonPaths(json_args: str):
  """Returns the src and dest from the json path list string.

  Multiple srcs can be mapped to the same dest, dest is the last element in the
  args.

  Args:
    json_args: json args to COPY/ADD instruction. e.g. `["src1", "src2",
      "dest"]`

  Returns:
    A tuple of (src_list, dest).
  """
  try:
    paths = json.loads(json_args)
  except json.JSONDecodeError as e:
    raise ValueError(
        f'Invalid JSON array for COPY/ADD instruction: {json_args}'
    ) from e

  if len(paths) < 2:
    raise ValueError(
        'Expected at least 2 elements in JSON array for COPY/ADD instruction'
        f' found {len(paths)}: {json_args}'
    )

  return paths[:-1], paths[-1]


def _GetSrcDestPath(args: str):
  """Returns the src and dest from the args string.

  Multiple srcs can be mapped to the same dest, dest is the last element in the
  args.

  Args:
    args: The args to COPY/ADD instruction. e.g. `src1 src2 dest`

  Returns:
    A tuple of (src_list, dest).
  """
  try:
    paths = shlex.split(args)
  except ValueError:
    # Fallback or error if splitting fails
    paths = args.split()

  # Unsupported path format. Used by more complex COPY/ADD instructions.
  if any(path.startswith('--') for path in paths):
    return None, None

  if len(paths) < 2:
    raise ValueError(
        'Expected at least 2 elements in args for COPY/ADD instruction'
        f' found {len(paths)}: {args}'
    )
  return paths[:-1], paths[-1]


def _ValidateSrcPath(src: str, abs_source_dir: str):
  """Ensure src path in correct scope based on source directory."""

  # Docker does not support absolute source paths for COPY/ADD instructions.
  is_docker_supported_src_path = not os.path.isabs(src)
  if not is_docker_supported_src_path:
    log.warning(
        f'Skipping {src}: absolute source paths are not supported by docker'
        ' COPY/ADD'
    )
    return False

  # Check if src is outside the source context. We restrict sync from
  # accessing files outside the source context to prevent potential
  # security issues.
  try:
    abs_src = os.path.join(abs_source_dir, os.path.normpath(src))
    rel_path = os.path.relpath(abs_src, abs_source_dir)
    is_src_path_outside_of_src_dir = (
        rel_path.startswith(os.pardir + os.sep) or rel_path == os.pardir
    )

    if is_src_path_outside_of_src_dir:
      log.warning(f'Skipping {src}: path is outside source context')
      return False
  except ValueError:
    # On Windows, relpath fails if paths are on different drives
    log.warning(f'Skipping {src}: path is outside source context')
    return False

  return True


def _CreateSyncRules(
    srcs: Sequence[str],
    dest: str,
    dest_workdir: str,
    abs_source_dir: str,
) -> Sequence[SyncRule]:
  """Creates sync rules from the parsed Dockerfile."""
  sync_rules = []

  abs_dest = (
      posixpath.join(dest_workdir, dest) if not posixpath.isabs(dest) else dest
  )

  # Watcher expects src relative to abs_source_dir
  for src in srcs:
    abs_src = os.path.join(abs_source_dir, os.path.normpath(src))

    if not _ValidateSrcPath(src, abs_source_dir):
      raise ValueError(f'Invalid path found in Dockerfile: {src}')

    src_is_file = os.path.isfile(abs_src)
    dest_is_dir = abs_dest.endswith(posixpath.sep) or len(srcs) > 1
    effective_dest = abs_dest
    if dest_is_dir and src_is_file:
      effective_dest = posixpath.join(abs_dest, os.path.basename(abs_src))

    effective_dest = posixpath.normpath(effective_dest)

    # Do not create rel_src before validating src, may cause error if src
    # is on a different drive than abs_source_dir
    rel_src = os.path.relpath(abs_src, abs_source_dir)

    # sync rules should have src relative to abs_src_dir
    sync_rules.append(SyncRule(rel_src, effective_dest))

  return sync_rules


def _GetBuildpackSyncRules() -> Sequence[SyncRule]:
  """Returns default sync rules to be used for Buildpacks."""
  return [SyncRule('.', '/workspace')]


def GenerateRules(abs_source_dir: str, dockerfile_name=_DOCKERFILE_NAME):
  """Parses Dockerfile and returns sync rules.

  Sync rules are mapping for files or folder from developer local directory to
  the Cloud Run container.

  Args:
    abs_source_dir: Absolute path to the source directory.
    dockerfile_name: Name of the Dockerfile.

  Returns:
    List of sync rules.
  """
  rules = []
  dest_workdir = posixpath.sep

  dockerfile_path = os.path.join(abs_source_dir, dockerfile_name)

  if not os.path.exists(dockerfile_path):
    return _GetBuildpackSyncRules()

  lines = dockerfile_parser.ReadDockerfile(dockerfile_path)

  for line in lines:
    dest_workdir = _CheckAndUpdateWorkdir(line, dest_workdir)

    parts = line.split(None, 1)
    if len(parts) != 2:
      raise ValueError(
          f'Error parsing line in {dockerfile_name}: {line}. '
          'Expected format: INSTRUCTION <args>'
      )

    instruction = parts[0].upper()
    if instruction not in ('COPY', 'ADD'):
      continue

    value = parts[1].strip()  # value after COPY or ADD instruction

    # Multiple srcs can be mapped to the same dest in a single instruction.
    # Check if args are in JSON array format
    # e.g. COPY ["src1", "src2", "dest"]
    if value.startswith('['):
      srcs, dest = _GetSrcDestJsonPaths(value)
    else:
      srcs, dest = _GetSrcDestPath(value)

    if not srcs or not dest:
      continue

    # Resolve relative destination against current_workdir
    sync_rules = _CreateSyncRules(srcs, dest, dest_workdir, abs_source_dir)
    rules.extend(sync_rules)

  return rules


def GetDestPaths(
    abs_src_path: str,
    abs_source_dir: str,
    sync_rules: Sequence[SyncRule],
):
  """Checks sync rules and returns container paths for the src path."""

  rel_src_path = os.path.relpath(abs_src_path, abs_source_dir)

  dest_paths = []

  # Check all sync rules as single src can be mapped to multiple destinations.
  for rule in sync_rules:
    src = rule.src
    dest = rule.dest

    if src == os.curdir:
      sub_path = rel_src_path
    elif rel_src_path == src:
      sub_path = ''
    elif rel_src_path.startswith(src + os.sep):
      sub_path = rel_src_path[len(src) :].lstrip(os.sep)
    else:
      continue

    if sub_path:
      # Convert the separator for the container which expects POSIX paths.
      sub_path = sub_path.replace(os.sep, posixpath.sep)
      dest_paths.append(posixpath.join(dest, sub_path))
    else:
      dest_paths.append(dest)

  return dest_paths
