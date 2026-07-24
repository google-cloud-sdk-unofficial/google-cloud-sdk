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
"""Utilities for bulk operations on disks."""


import json
import os

from apitools.base.protorpclite import messages as protorpc_messages
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core.util import encoding
from googlecloudsdk.core.util import files

BUILD_WORKING_DIRECTORY = encoding.GetEncodedValue(
    os.environ, 'BUILD_WORKING_DIRECTORY'
)


#
# Sets the resources name field on the request, working around apitools bugs.
#
# In the set_labels.proto definition, the `BulkSetLabelsRequest` method
# contains an `optional string name = 1` field, configured with `json_name =
# "resource"`. Currently, the apitools code generator incorrectly drops this
# field from the generated Python `BulkSetLabelsRequest` class.
#
# If we try assigning `request.resource` or `request.name`, we get an
# `AttributeError`. To ensure the Compute API receives the target disk in the
# JSON body, we must forcefully inject both `name` and `resource` into the
# payload using `set_unrecognized_field()`.
#
def HandleUnrecognizedFields(request, request_data):
  """Sets the resource/name field on the request, working around apitools bugs."""
  try:

    request.resource = request_data['name']

  except AttributeError:
    try:

      request.name = request_data['name']

    except AttributeError:
      if hasattr(request, 'set_unrecognized_field'):
        request.set_unrecognized_field(
            'name',
            request_data['name'],
            protorpc_messages.Variant.STRING,
        )
        request.set_unrecognized_field(
            'resource',
            request_data['name'],
            protorpc_messages.Variant.STRING,
        )

  return request


def ReadDataFromFile(file_path):
  """Reads JSON data from the specified file path."""
  full_path = files.ExpandHomeDir(file_path)
  if not os.path.isabs(full_path):
    cwd = BUILD_WORKING_DIRECTORY or files.GetCWD()
    full_path = os.path.join(cwd, full_path)

  try:

    content = files.ReadFileContents(full_path)
    deserialized_data = json.loads(content)

  except files.MissingFileError as error:
    raise exceptions.InvalidArgumentException(
        parameter_name='--source',
        message=f'No such file or directory: {file_path}',
    ) from error
  except ValueError as error:
    raise exceptions.InvalidArgumentException(
        parameter_name='--source',
        message=f'Could not parse JSON: {error}',
    ) from error

  return deserialized_data


def ValidateSourceDataOuter(data):
  """Validates the overall structure of the JSON list from --source."""
  if not data:
    raise exceptions.InvalidArgumentException(
        parameter_name='--source',
        message='List of requests cannot be empty.',
    )

  if not isinstance(data, list):
    raise exceptions.InvalidArgumentException(
        parameter_name='--source',
        message='Value must be a JSON list of disk label requests.',
    )


def ValidateSourceDataInner(data):
  """Validates each item within the JSON list from --source."""
  for i, data_item in enumerate(data):
    if not isinstance(data_item, dict):
      raise exceptions.InvalidArgumentException(
          parameter_name='--source',
          message=f'Item at index {i} is not a valid JSON object.',
      )

    if 'name' not in data_item:
      raise exceptions.InvalidArgumentException(
          parameter_name='--source',
          message=f'Item at index {i} is missing the required "name" field.',
      )


def FormRequests(messages, requests_data):
  """Converts JSON request data list into a list of BulkSetLabelsRequest."""
  requests = []

  for request_data in requests_data:
    labels_msg = messages.BulkSetLabelsRequest.LabelsValue()

    if 'labels' in request_data and request_data['labels']:
      for key, value in request_data['labels'].items():
        labels_msg.additionalProperties.append(
            messages.BulkSetLabelsRequest.LabelsValue.AdditionalProperty(
                key=key, value=str(value)
            )
        )

    request = messages.BulkSetLabelsRequest(labels=labels_msg)
    request = HandleUnrecognizedFields(request, request_data)

    if 'label_fingerprint' in request_data:
      request.labelFingerprint = request_data['label_fingerprint'].encode(
          'utf-8'
      )

    requests.append(request)

  return requests


def FromResponse(requests, responses):
  """Formats the API response for bulk operations."""
  responses_list = list(responses)
  final_response = {'updatedDisksCount': len(requests)}

  if (
      responses_list
      and hasattr(responses_list[0], 'name')
      and responses_list[0].name
  ):
    final_response['operationId'] = responses_list[0].name

  return final_response
