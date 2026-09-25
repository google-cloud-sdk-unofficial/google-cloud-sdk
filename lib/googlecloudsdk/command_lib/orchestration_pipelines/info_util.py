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
"""Utilities for orchestration pipelines info command."""

import re
from typing import Any, Dict
from googlecloudsdk.core import config

_DOCS_URL = 'https://docs.cloud.google.com/sdk/docs/release-notes'
_UNKNOWN_VERSION = 'UNKNOWN'


def GetModelVersion() -> str:
  """Retrieves orchestration-pipelines-models version as <major>.<minor>.X."""
  try:
    import orchestration_pipelines_models  # pylint: disable=g-import-not-at-top

    version = getattr(orchestration_pipelines_models, '__version__', None)
    if version:
      match = re.match(r'^v?(\d+)\.(\d+)', str(version))
      return f'{match.group(1)}.{match.group(2)}.X' if match else str(version)
  except (ImportError, AttributeError):
    pass
  return _UNKNOWN_VERSION


def GetInfo() -> Dict[str, Any]:
  """Gathers all orchestration pipelines information as a dictionary."""
  model_version = GetModelVersion()
  return {
      'model_version': model_version,
      'gcloud_sdk_version': config.CLOUD_SDK_VERSION,
      'notes': (
          'This version of the CLI supports features up to Model Version'
          f' {model_version}. Newer features require updating the Google Cloud'
          f' CLI. More details about package versions:\n{_DOCS_URL}\n'
          'To update your Google Cloud CLI:\n'
          'gcloud components update'
      ),
  }
