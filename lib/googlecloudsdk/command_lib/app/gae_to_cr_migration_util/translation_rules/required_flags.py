# -*- coding: utf-8 -*- #
# Copyright 2025 Google LLC. All Rights Reserved.
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

"""Add required flags to output gcloud run deploy command."""

from collections.abc import Mapping, Sequence
import os
from googlecloudsdk.command_lib.app.gae_to_cr_migration_util.common import util


def translate_add_required_flags(
    input_data: Mapping[str, any],
    source_path: str,
    runtime_base_image: str | None,
) -> Sequence[str]:
  """Add required flags to gcloud run deploy command.

  Args:
    input_data: A mapping containing the translated data from app.yaml.
    source_path: The path to the application source code.
    runtime_base_image: The base image to use for the runtime, returned by
      export_image_api response (only for image based migration).

  Returns:
    A sequence of strings representing the required flags.
  """
  is_flex = util.is_flex_env(input_data)
  migration_tool = (
      'gcloud-app-migrate-flexible-v1'
      if is_flex
      else 'gcloud-app-migrate-standard-v1'
  )
  required_flags = [
      f'--labels={_get_labels(migration_tool=migration_tool)}'
  ]

  if not is_flex:
    base_image = runtime_base_image or input_data['runtime']
    if source_path and _check_dockerfile_exists(source_path):
      required_flags.extend([
          '--clear-base-image',
      ])
    else:
      if base_image:
        required_flags.append(f'--base-image={base_image}')
  required_flags.append('--no-cpu-throttling')

  return required_flags


def _get_labels(*, migration_tool: str) -> str:
  """Get labels for gcloud run deploy command."""
  return f'migrated-from=app-engine,migration-tool={migration_tool}'


def _check_dockerfile_exists(source_path: str) -> bool:
  """Check for a Dockerfile in the source directory.

  This function verifies if a Dockerfile exists in the same directory
  as the provided `source_path` (typically the app.yaml file).

  Args:
    source_path: The path to the application source code (e.g., app.yaml).

  Returns:
    True if a Dockerfile exists in the same directory as `source_path`, False
    otherwise.
  """
  dockerfile_path = os.path.join(
      os.path.dirname(source_path), 'Dockerfile'
  )
  return os.path.exists(dockerfile_path)
