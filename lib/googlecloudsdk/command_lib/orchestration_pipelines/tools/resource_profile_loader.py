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
"""Utilities for loading external resource profiles."""

import contextlib
import os
from typing import Any, Dict, Optional

from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.core import yaml


def load_external_resource_profile(
    resource_profile: Dict[str, Any], work_dir: str
) -> Optional[Dict[str, Any]]:
  """Loads an external YAML profile from a GCS URI or a local path.

  Args:
      resource_profile: The dictionary containing 'externalConfigPath' or
        'path'.
      work_dir: The base working directory to resolve local relative paths
        against.

  Returns:
      A dictionary representing the parsed YAML file, or None if loading fails.
  """
  if "externalConfigPath" in resource_profile:
    try:
      object_ref = storage_util.ObjectReference.FromUrl(
          resource_profile.get("externalConfigPath")
      )
      storage_client = storage_api.StorageClient()
      with contextlib.closing(storage_client.ReadObject(object_ref)) as f:
        yaml_content = f.read()
        if isinstance(yaml_content, bytes):
          yaml_content = yaml_content.decode("utf-8")
        return yaml.load(yaml_content)
    except (IOError, ValueError, yaml.YAMLParseError):
      pass

  if "path" in resource_profile:
    profile_path = os.path.join(work_dir, resource_profile.get("path"))
    try:
      return yaml.load_path(profile_path)
    except (IOError, yaml.YAMLParseError):
      pass

  return None
