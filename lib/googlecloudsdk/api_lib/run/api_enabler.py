# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Utilities for checking and enabling necessary APIs."""

import urllib.parse as urlparse

from googlecloudsdk.api_lib.services import enable_api
from googlecloudsdk.api_lib.services import exceptions as services_exceptions
from googlecloudsdk.api_lib.services import services_util
from googlecloudsdk.api_lib.services import serviceusage
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io

_RUN_API_NAMES = frozenset(
    ['run.googleapis.com', 'staging-run.sandbox.googleapis.com']
)


def get_run_api():
  endpoint = properties.VALUES.api_endpoint_overrides.run.Get()
  if endpoint:
    api = urlparse.urlparse(endpoint).hostname
    if api in _RUN_API_NAMES:
      return api
  return 'run.googleapis.com'


def _check_preconditions():
  """Checks if API enablement preconditions are met."""
  if not properties.VALUES.core.should_prompt_to_enable_api.GetBool():
    # no need to even check if prompting is disabled.
    return False
  endpoint_mode = properties.VALUES.regional.endpoint_mode.Get()
  if (
      properties.VALUES.regional.endpoint_compatibility.Get()
      and endpoint_mode == properties.VALUES.regional.REGIONAL
  ):
    # Service usage API does not support regional endpoints.
    return False
  return True


def _batch_enable_apis(project_id, apis, message, prompt_string, print_op):
  """Enables the given APIs in batch with a prompt."""
  console_io.PromptContinue(
      default=True,
      cancel_on_no=True,
      message=message,
      prompt_string=prompt_string,
  )

  log.status.Print('Enabling APIs on project [{0}]...'.format(project_id))
  op = serviceusage.BatchEnableApiCall(project_id, apis)
  if not op.done:
    op = services_util.WaitOperation(op.name, serviceusage.GetOperation)
    if print_op:
      services_util.PrintOperation(op)


def enable_apis(project_id, required_apis):
  """Ensure the given APIs are enabled for the specified project without checking enablement first."""
  if not required_apis:
    return True
  if not _check_preconditions():
    return False

  apis_to_enable = '\n\t'.join(required_apis)
  message = (
      'Ensuring the following APIs are enabled on project [{0}]:\n\t{1}'.format(
          project_id, apis_to_enable
      )
  )
  prompt_string = 'Do you want to continue (this will take a few minutes)?'

  _batch_enable_apis(
      project_id, required_apis, message, prompt_string, print_op=True
  )
  return True


def check_and_enable_apis(project_id, required_apis):
  """Ensure the given APIs are enabled for the specified project."""
  if not required_apis:
    return True
  if not _check_preconditions():
    return False
  try:
    apis_not_enabled = get_disabled_apis(project_id, required_apis)
  except services_exceptions.GetServicePermissionDeniedException:
    return False
  if apis_not_enabled:
    apis_to_enable = '\n\t'.join(apis_not_enabled)
    message = (
        'The following APIs are not enabled on project [{0}]:\n\t{1}'.format(
            project_id, apis_to_enable
        )
    )
    prompt_string = (
        'Do you want enable these APIs to '
        + 'continue (this will take a few minutes)?'
    )
    _batch_enable_apis(
        project_id, apis_not_enabled, message, prompt_string, print_op=False
    )
  return True


def get_disabled_apis(project_id, required_apis):
  apis_not_enabled = [
      # iterable is sorted for scenario tests.  The order of API calls
      # should happen in the same order each time for the scenario tests.
      api
      for api in sorted(required_apis)
      if not enable_api.IsServiceEnabled(project_id, api)
  ]
  return apis_not_enabled
