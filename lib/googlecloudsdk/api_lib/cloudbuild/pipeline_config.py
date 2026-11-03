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
"""Parse pipeline config files and derive their update masks."""

import collections
import os

from apitools.base.py import encoding as apitools_encoding
from googlecloudsdk.calliope import exceptions as c_exceptions
from googlecloudsdk.core import yaml
from googlecloudsdk.core.resource import resource_property
from googlecloudsdk.core.util import files

# Fields of the Pipeline resource that the user is allowed to set. Everything
# else on the message is OUTPUT_ONLY, so it must never reach the update mask:
# the server rejects a mask that names an output-only field, which would make
# re-applying an exported pipeline fail. The order is significant only in that
# it fixes the order of the paths in the generated mask.
_MUTABLE_FIELDS = (
    'config',
    'displayName',
    'description',
    'serviceAccount',
    'annotations',
    'labels',
)

# Empty defaults substituted when a mutable field is explicitly null or blank
# in YAML (e.g. `displayName:` or `labels: null`). `apitools` decodes `None` by
# resetting the field on the message, which would omit it from the update mask
# instead of clearing it on the server.
_MUTABLE_FIELD_DEFAULTS = {
    'config': {},
    'displayName': '',
    'description': '',
    'serviceAccount': '',
    'annotations': {},
    'labels': {},
}

# Resource identity and server-generated fields to drop from the request body.
# `name` is resolved via the resource argument (and passed as the PATCH target
# path) rather than sent in the body. Most output-only fields are harmless to
# leave in the parsed message, because the mask allowlist keeps them out of the
# update. The etag is the exception: the server validates it, so an exported
# pipeline could not be re-applied without first hitting a checksum mismatch.
_IGNORED_FIELDS = ('etag', 'name')

# Top-level key that declares the pipeline's triggers inline. It is not a field
# of the Pipeline resource: `triggers` lists PipelineTrigger definitions, so it
# is split off before the pipeline is decoded and handed back raw to be
# converted by pipeline_trigger_config.LoadNestedTriggers.
_TRIGGERS_FIELD = 'triggers'

# A decoded pipeline config file.
#
# Attributes:
#   pipeline: messages.Pipeline, the decoded pipeline.
#   triggers: list|None, the raw `triggers` list, or None if the file has none.
PipelineConfig = collections.namedtuple(
    'PipelineConfig', ['pipeline', 'triggers']
)


def ComputeUpdateMask(pipeline):
  """Computes the update mask covering the fields set on a pipeline.

  A field is included whenever the definition assigns it a value, even if that
  value is empty (e.g. `displayName: ""`), so that a field can be cleared
  declaratively. Fields the definition omits are absent from the mask and are
  therefore left untouched by the server.

  Args:
    pipeline: messages.Pipeline, the pipeline to derive the mask from.

  Raises:
    c_exceptions.BadFileException: If the pipeline sets no mutable field. An
      empty mask must never be sent, because the server treats a missing mask
      as a request to replace every field of the stored pipeline.

  Returns:
    str, a comma-separated update mask.
  """
  fields = [
      resource_property.ConvertToSnakeCase(name)
      for name in _MUTABLE_FIELDS
      if pipeline.get_assigned_value(name) is not None
  ]
  if not fields:
    raise c_exceptions.BadFileException(
        'Pipeline definition does not set any of the following fields: [{}].'
        .format(', '.join(_MUTABLE_FIELDS))
    )
  return ','.join(fields)


def _ReadYamlMapping(path):
  """Reads a pipeline config file into a dict.

  Args:
    path: str, path to the JSON or YAML data to be decoded.

  Raises:
    c_exceptions.BadFileException: If the file is missing, cannot be parsed, or
      does not hold a mapping.

  Returns:
    dict, the decoded contents of the file.
  """
  path = files.ExpandHomeDir(path)
  if not os.path.exists(path) or os.path.isdir(path):
    raise c_exceptions.BadFileException(
        'Pipeline configuration file [{}] does not exist.'.format(path)
    )

  try:
    data = yaml.load_path(path)
  except Exception as e:
    raise c_exceptions.BadFileException(
        'Could not parse YAML/JSON from file [{}]: {}'.format(path, e)
    )

  if not data:
    raise c_exceptions.BadFileException(
        'Pipeline configuration file [{}] is empty.'.format(path)
    )

  if not isinstance(data, dict):
    raise c_exceptions.BadFileException(
        'Pipeline configuration file [{}] must contain a YAML mapping.'.format(
            path
        )
    )

  return data


def ExtractPipelineId(path):
  """Reads the pipeline ID or resource name declared by a pipeline config file.

  This resolves the pipeline resource argument when the user gives no ID on the
  command line. It deliberately reports any problem with the file as a missing
  ID rather than raising, leaving LoadPipelineConfigFromPath as the single
  place that diagnoses malformed definitions, since it produces a far more
  precise message than resource argument resolution could.

  Args:
    path: str, path to the JSON or YAML data to be decoded.

  Returns:
    str, the ID or resource name in `name`, or None if the file declares none.
  """
  try:
    data = _ReadYamlMapping(path)
  except c_exceptions.BadFileException:
    return None

  name = data.get('name')
  if not isinstance(name, str) or not name:
    return None

  return name


def LoadPipelineConfigFromPath(path, messages):
  """Loads a pipeline config file into a Pipeline message.

  The file may also declare the pipeline's triggers inline in a top-level
  `triggers` list, which is returned undecoded.

  Args:
    path: str, path to the JSON or YAML data to be decoded.
    messages: module, the messages module that has a Pipeline type.

  Raises:
    c_exceptions.BadFileException: If the file is missing, cannot be parsed, or
      does not describe a pipeline.

  Returns:
    PipelineConfig, the decoded pipeline and its raw nested triggers list.
  """
  data = _ReadYamlMapping(path)
  clean_data = dict(data)

  # The nested triggers section is not a pipeline field, so it must come out
  # before the decoder sees it or it would be reported as unrecognized.
  triggers = clean_data.pop(_TRIGGERS_FIELD, None)

  for field in _IGNORED_FIELDS:
    clean_data.pop(field, None)

  for field, empty_val in _MUTABLE_FIELD_DEFAULTS.items():
    if field in clean_data and clean_data[field] is None:
      clean_data[field] = empty_val

  try:
    pipeline = apitools_encoding.PyValueToMessage(messages.Pipeline, clean_data)
  except Exception as e:
    raise c_exceptions.BadFileException(
        'Failed to parse Pipeline definition into API message: {}'.format(e)
    )

  # Keys that match no field are silently dropped by the decoder, which would
  # turn a typo into a definition that applies cleanly but does nothing.
  unrecognized_fields = pipeline.all_unrecognized_fields()
  if unrecognized_fields:
    raise c_exceptions.BadFileException(
        'Pipeline configuration file [{}] contains unrecognized fields: [{}].'
        .format(path, ', '.join(sorted(unrecognized_fields)))
    )

  return PipelineConfig(pipeline=pipeline, triggers=triggers)
