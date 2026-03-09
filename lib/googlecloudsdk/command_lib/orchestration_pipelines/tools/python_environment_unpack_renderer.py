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
"""Utilities for rendering initialization actions for gce pipelines."""

import pathlib
import pkgutil
from typing import Text

from googlecloudsdk.core.util import files


def render_init_action(
    work_dir: pathlib.Path,
    libs_dir: Text,
    env_name: Text,
    gcs_archive_path: Text,
) -> pathlib.Path:
  """Renders the python_environment_unpack.sh template with dynamic values."""
  template = pkgutil.get_data(
      "googlecloudsdk.command_lib.orchestration_pipelines.tools",
      "python_environment_unpack.sh",
  ).decode("utf-8")

  # Replace the default values in the template with dynamic ones.
  rendered = template.replace(
      "@@GCS_ARCHIVE_PATH@@",
      gcs_archive_path,
  )
  rendered = rendered.replace(
      "@@LOCAL_INSTALL_DIR@@",
      f"/opt/{env_name}",
  )
  rendered = rendered.replace(
      "@@LIBS_DIR@@",
      libs_dir,
  )

  init_action_path = work_dir / "python_environment_unpack.sh"
  files.WriteFileContents(init_action_path, rendered)
  return init_action_path
