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
"""Data class holding local context for a source containers."""

import dataclasses
from typing import Any


@dataclasses.dataclass
class SourceContainerContext:
  """Data class holding local context for a source container."""

  name: str  # container name
  base_image: str = None  # base image to be used for deploy/build
  source: str = None  # local source code location
  source_bucket: str = None  # GCS bucket to use for upload


@dataclasses.dataclass
class LegacyBuildSourceContainerContext:
  """Data class holding local context for a legacy SubmitBuild source container."""

  build_image: str = None  # build image to be used for deploy
  build_pack: Any = None  # build pack to be used for deploy
  build_source: str = None  # build source to be used for deploy
  repo_to_create: str = None  # AR repo to create
  is_function: bool = False  # whether the container specified --function
  base_image: str = None  # base image to be used for deploy
  build_service_account: str = None  # service account to be used for build
  build_env_vars: dict[str, str] = None  # build env vars to be used for build
  build_worker_pool: str = None  # build worker pool to be used for build
  build_machine_type: str = None  # build machine type to be used for build
  deploy_from_source_container_name: str = ''  # container name
  enable_automatic_updates: bool = None  # whether to enable automatic updates
  source_bucket: str = None  # GCS bucket to use for upload
