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
"""Data models for locally packaged pipeline artifacts."""

import dataclasses
import pathlib


@dataclasses.dataclass(frozen=True)
class PackagingContext:
  """Pipeline and environment settings for packaging an action."""

  pipeline_id: str
  # The deployment environment; also the dbt target name.
  target: str
  staging_dir: pathlib.Path


@dataclasses.dataclass(frozen=True)
class StagedFile:
  """Local file staged for upload to Cloud Storage."""

  # Local path to the packaged .tar.gz file on disk.
  local_path: pathlib.Path
  # Object name relative to the version prefix, e.g. `dbt_gold.tar.gz`.
  relative_path: str
  sha256: str


@dataclasses.dataclass(frozen=True)
class PackagedArtifact:
  """Staged files produced by packaging a pipeline action."""

  action_name: str
  files: tuple[StagedFile, ...]
