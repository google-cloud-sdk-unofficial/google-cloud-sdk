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

# Server-generated fields to drop from the definition. Most output-only fields
# are harmless to leave in the parsed message, because the mask allowlist keeps
# them out of the update. The etag is the exception: the server validates it,
# so an exported pipeline could not be re-applied without first hitting a
# checksum mismatch.
_IGNORED_FIELDS = ('etag',)

# The `kind` of the Kubernetes-style layout that this command accepts.
_DOCUMENT_KIND = 'Pipeline'

# Keys nested under `metadata` in the Kubernetes-style layout that are
# top-level fields on the Pipeline resource.
_LIFTED_METADATA_FIELDS = ('labels', 'annotations')


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
  """Reads the pipeline ID declared by a pipeline config file.

  This resolves the pipeline resource argument when the user gives no ID on the
  command line. It deliberately reports any problem with the file as a missing
  ID rather than raising, leaving LoadPipelineConfigFromPath as the single
  place that diagnoses malformed definitions, since it produces a far more
  precise message than resource argument resolution could.

  Args:
    path: str, path to the JSON or YAML data to be decoded.

  Returns:
    str, the ID in `metadata.name`, or None if the file declares none.
  """
  try:
    data = _ReadYamlMapping(path)
  except c_exceptions.BadFileException:
    return None

  # Only the Kubernetes-style layout carries a bare ID. The flat layout has
  # nowhere to put one, because `name` on the Pipeline resource is the full
  # relative name rather than an ID.
  if data.get('kind') != _DOCUMENT_KIND:
    return None

  metadata = data.get('metadata')
  if not isinstance(metadata, dict):
    return None

  return metadata.get('name')


def LoadPipelineConfigFromPath(path, messages):
  """Loads a pipeline config file into a Pipeline message.

  Both the flat layout, whose keys are the fields of the Pipeline resource, and
  the Kubernetes-style layout, which wraps those fields in `apiVersion`, `kind`
  and `metadata`, are accepted.

  Args:
    path: str, path to the JSON or YAML data to be decoded.
    messages: module, the messages module that has a Pipeline type.

  Raises:
    c_exceptions.BadFileException: If the file is missing, cannot be parsed, or
      does not describe a pipeline.

  Returns:
    messages.Pipeline, the decoded pipeline.
  """
  data = _ReadYamlMapping(path)
  clean_data = dict(data)

  if clean_data.get('kind') == _DOCUMENT_KIND:
    metadata = clean_data.pop('metadata', None)
    if isinstance(metadata, dict):
      # Labels and annotations are nested under `metadata` in the
      # Kubernetes-style layout, but are top-level fields on the Pipeline
      # resource, so lift them instead of dropping them with the metadata.
      for field in _LIFTED_METADATA_FIELDS:
        if field in metadata and field not in clean_data:
          clean_data[field] = metadata[field]
    clean_data.pop('apiVersion', None)
    clean_data.pop('kind', None)

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

  return pipeline
