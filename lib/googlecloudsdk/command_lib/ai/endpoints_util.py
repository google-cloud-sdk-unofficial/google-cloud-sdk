# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Utilities for AI Platform endpoints commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import io

from googlecloudsdk.command_lib.ai import errors
from googlecloudsdk.core import resources
from googlecloudsdk.core import yaml
from googlecloudsdk.core.console import console_io


def ParseOperation(operation_name):
  """Parse operation resource to the operation reference object.

  Args:
    operation_name: The operation resource to wait on

  Returns:
    The operation reference object
  """
  if '/endpoints/' in operation_name:
    try:
      return resources.REGISTRY.ParseRelativeName(
          operation_name,
          collection='aiplatform.projects.locations.endpoints.operations',
      )
    except resources.WrongResourceCollectionException:
      pass
  return resources.REGISTRY.ParseRelativeName(
      operation_name, collection='aiplatform.projects.locations.operations'
  )


def _LoadYaml(file_path, sdk_method):
  """Loads a YAML file."""
  data = console_io.ReadFromFileOrStdin(file_path, binary=True)
  with io.BytesIO(data) as f:
    try:
      return yaml.load(f)
    except ValueError:
      raise errors.InvalidInstancesFileError(
          f'Input is not in JSON format. See `gcloud ai endpoints {sdk_method}'
          ' --help` for details.'
      )


def ReadInstancesFromArgs(json_request):
  """Reads the instances from the given file path ('-' for stdin).

  Args:
    json_request: str or None, a path to a file ('-' for stdin) containing the
      JSON body of a prediction request.

  Returns:
    A list of instances.

  Raises:
    InvalidInstancesFileError: If the input file is invalid (invalid format or
        contains too many/zero instances), or an improper combination of input
        files was given.
  """
  request = _LoadYaml(json_request, sdk_method='predict')

  if not isinstance(request, dict):
    raise errors.InvalidInstancesFileError(
        'Input instances are not in JSON format. '
        'See `gcloud ai endpoints predict --help` for details.'
    )

  if 'instances' not in request:
    raise errors.InvalidInstancesFileError(
        'Invalid JSON request: missing "instances" attribute'
    )

  if not isinstance(request['instances'], list):
    raise errors.InvalidInstancesFileError(
        'Invalid JSON request: "instances" must be a list'
    )

  return request


def ReadInputsFromArgs(json_request):
  """Validates and reads json request for Direct Prediction."""
  request = _LoadYaml(json_request, sdk_method='direct-predict')
  if 'inputs' not in request:
    raise errors.InvalidInstancesFileError('Input json must contain "inputs"')
  return request


def ReadInputFromArgs(json_request):
  """Validates and reads json request for Direct Raw Prediction."""
  request = _LoadYaml(json_request, sdk_method='direct-raw-predict')
  if 'input' not in request:
    raise errors.InvalidInstancesFileError('Input json must contain "input"')
  if 'method_name' not in request and 'methodName' not in request:
    raise errors.InvalidInstancesFileError(
        'Input json must contain "method_name" or "methodName"'
    )
  return request


def GetDefaultFormat(predictions, key_name='predictions'):
  """Get default output format for prediction results."""
  if not isinstance(predictions, list):
    # This usually indicates some kind of error case, so surface the full API
    # response
    return 'json'
  elif not predictions:
    return None
  # predictions is guaranteed by API contract to be a list of similarly shaped
  # objects, but we don't know ahead of time what those objects look like.
  elif isinstance(predictions[0], dict):
    keys = ', '.join(sorted(predictions[0].keys()))
    return """
          table(
              {}:format="table(
                  {}
              )"
          )""".format(key_name, keys)

  else:
    return 'table[no-heading]({})'.format(key_name)
