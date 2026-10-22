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
"""Loads pipeline YAML files for the Serverless Orchestration API."""

import argparse
from collections.abc import Mapping
import dataclasses
import pathlib
from typing import Any

from googlecloudsdk.command_lib.orchestration_pipelines.serverless_orchestration import errors

DEFAULT_PROFILE_NAME = "dcs_bigquery"


@dataclasses.dataclass(frozen=True)
class DbtAction:
  """A dbt action parsed from the pipeline YAML."""

  name: str
  # Absolute path of the dbt project directory.
  project_directory: pathlib.Path
  command: str = "build"
  select: tuple[str, ...] = ()
  variables: Mapping[str, Any] = dataclasses.field(default_factory=dict)
  # Literal `profileConfig` values, rendered into `profiles.yml` when packaging.
  profile_config: Mapping[str, Any] = dataclasses.field(default_factory=dict)
  dbt_version: str | None = None
  full_refresh: bool = False


@dataclasses.dataclass(frozen=True)
class LoadedPipeline:
  """A pipeline YAML resolved against the command-line arguments."""

  pipeline_id: str
  project: str
  location: str
  # The deployment environment (`--environment`); also the dbt target name.
  target: str
  service_account: str | None
  # Bucket name without `gs://`, from `deployment.yaml` or the
  # `dcs-artifacts-<project>-<location>` default.
  artifact_bucket: str
  base_dir: pathlib.Path
  actions: tuple[DbtAction, ...]
  # The parsed pipeline YAML, for fields the compiler maps verbatim (e.g.
  # `triggers`).
  raw: Mapping[str, Any]
  profile_name: str = DEFAULT_PROFILE_NAME


def LoadPipeline(args: argparse.Namespace) -> LoadedPipeline:
  """Loads and validates the pipeline YAML selected by `args`.

  Args:
    args: The parsed command-line arguments.

  Returns:
    The typed pipeline model.

  Raises:
    errors.PipelineLoadError: If the pipeline cannot be resolved or is invalid.
  """
  # TODO(b/567520802): Resolve the file (`deployment.yaml` for `--environment`
  # or `./pipeline.yaml`), parse it, require `runner: orchestration_service`,
  # resolve project/location/artifact bucket and parse the dbt action.
  del args
  raise errors.NotImplementedYetError("LoadPipeline is not implemented yet.")
