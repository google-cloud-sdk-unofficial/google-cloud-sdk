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

import collections

from googlecloudsdk.api_lib.cloudbuild import cloudbuild_util
from googlecloudsdk.calliope import exceptions as c_exceptions
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


def LoadNestedTriggers(triggers, messages, path):
  """Converts the `triggers` section of a pipeline config file.

  Called by `gcloud builds pipelines apply` when a pipeline file declares its
  triggers inline. Every entry is converted before any RPC is sent, so a bad
  trigger stops the command up front rather than after the pipeline has
  already been written.

  Args:
    triggers: object, the raw `triggers` value from the pipeline file, or None.
    messages: module, the Cloud Build v1 messages module.
    path: str, path to the pipeline file, for error messages.

  Raises:
    c_exceptions.BadFileException: If `triggers` is not a valid list of named
      trigger mappings.
    cloudbuild_exceptions.ParseProtoException: If a trigger entry cannot be
      converted into a `PipelineTrigger` message.

  Returns:
    [(str, messages.PipelineTrigger)], `(trigger_id, trigger)` pairs in the
    order they appear in the file.
  """
  if triggers is None:
    return []
  entries = _ListEntries(triggers, path)
  return [
      (trigger_id, _BuildTrigger(raw, messages, trigger_id, path))
      for trigger_id, raw in entries.items()
  ]


def _ListEntries(triggers, path):
  """Validates a `triggers` list and indexes its entries by `name`."""
  if not isinstance(triggers, list):
    raise c_exceptions.BadFileException(
        '`triggers` in [{}] must be a list of trigger definitions.'.format(path)
    )

  entries = collections.OrderedDict()
  for i, entry in enumerate(triggers):
    location = 'triggers[{}] in [{}]'.format(i, path)
    if not isinstance(entry, dict):
      raise c_exceptions.BadFileException(
          '{} must be a mapping.'.format(location)
      )
    name = entry.get('name')
    if not isinstance(name, str) or not name.strip():
      raise c_exceptions.BadFileException(
          '{} must set `name` to the ID of the trigger.'.format(location)
      )
    name = name.strip()
    if '/' in name:
      raise c_exceptions.BadFileException(
          '{} must set `name` to a trigger ID, not a full resource name [{}].'
          .format(location, name)
      )
    if name in entries:
      raise c_exceptions.BadFileException(
          '`triggers` in [{}] defines trigger [{}] more than once.'.format(
              path, name
          )
      )
    entries[name] = entry
  return entries


def _BuildTrigger(raw, messages, trigger_id, path):
  """Converts a single raw trigger mapping into a PipelineTrigger message."""
  trigger = cloudbuild_util.LoadMessageFromStream(
      stream=yaml.dump(raw),
      msg_type=messages.PipelineTrigger,
      msg_friendly_name='Trigger [{}]'.format(trigger_id),
      skip_camel_case=_SKIP_CAMEL_CASE,
      path=path,
  )
  for field in _IGNORED_FIELDS:
    trigger.reset(field)
  return trigger

