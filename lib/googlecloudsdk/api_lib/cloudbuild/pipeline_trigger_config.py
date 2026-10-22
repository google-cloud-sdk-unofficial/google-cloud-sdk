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
"""Parse pipeline trigger configuration files for Cloud Build v1 API."""

from __future__ import annotations

from googlecloudsdk.api_lib.cloudbuild import cloudbuild_util
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import files

# UpdatePipelineTrigger uses this google.protobuf.FieldMask (proto snake_case
# field names, matching cloudbuild_util.MessageToFieldPaths and
# pipeline_config.ComputeUpdateMask) on every apply so the stored trigger is
# fully replaced: any mutable field left out of the file is cleared on the
# server instead of keeping its previous value.
FULL_UPDATE_MASK = ','.join([
    'annotations',
    'branch_push',
    'display_name',
    'git_repository_link',
    'labels',
    'merge_queue',
    'options',
    'params',
    'pub_sub',
    'pull_request',
    'repository_url',
    'tag_push',
    'topic',
    'webhook',
    'webhook_secret_version',
])

# Output-only and identifier fields that `triggers describe` emits. Resetting
# them on load lets an exported definition be fed straight back into `apply`.
_IGNORED_FIELDS = (
    'createTime',
    'deleteTime',
    'etag',
    'name',
    'reconciling',
    'uid',
    'updateTime',
)

# Map fields whose user-defined keys must not be converted from snake_case to
# camelCase by `cloudbuild_util.LoadMessageFromPath`.
_SKIP_CAMEL_CASE = ['annotations', 'labels', 'params']

_FRIENDLY_NAME = 'pipeline trigger config'


def LoadTriggerConfigFromPath(path, messages):
  """Loads a PipelineTrigger configuration file into a PipelineTrigger message.

  Args:
    path: str, path to the YAML file.
    messages: module, the Cloud Build v1 apitools messages module.

  Returns:
    messages.PipelineTrigger, the populated trigger message.
  """
  trigger = cloudbuild_util.LoadMessageFromPath(
      path=files.ExpandHomeDir(path),
      msg_type=messages.PipelineTrigger,
      msg_friendly_name=_FRIENDLY_NAME,
      skip_camel_case=_SKIP_CAMEL_CASE,
  )
  for field in _IGNORED_FIELDS:
    trigger.reset(field)
  return trigger


def ExtractTriggerId(path):
  """Returns the trigger ID from `name` in the file, or None.

  Used by the resource argument fallthrough before `Run()` loads the file, so
  I/O or parse errors return `None` and defer to `LoadTriggerConfigFromPath`.

  Args:
    path: str, path to the YAML file.

  Returns:
    str or None, the trigger ID from the file if present and non-empty.
  """
  try:
    data = yaml.load_path(files.ExpandHomeDir(path))
  except yaml.Error:
    return None
  if not isinstance(data, dict):
    return None
  name = data.get('name')
  if isinstance(name, str):
    return name.strip() or None
  return None
