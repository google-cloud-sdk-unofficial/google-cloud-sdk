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
"""Helper for fetching and displaying API keys for onboarding gcloud commands."""

from __future__ import annotations

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.services import apikeys
from googlecloudsdk.api_lib.util import exceptions as api_exceptions
from googlecloudsdk.core import log

# Display names of the Google Maps Platform demo API keys that the onboarding
# service provisions on eligible Starter Tier projects, in display order.
MAPS_DEMO_API_KEY_DISPLAY_NAMES = (
    'Maps Platform Demo API Client Key',
    'Maps Platform Demo API Server Key',
)


def FindMapsDemoApiKeys(project_name: str) -> list[tuple[str, str]]:
  """Finds the Maps Platform demo API keys provisioned on a project.

  Args:
    project_name: The project resource name or ID, e.g. `projects/my-project`
      or `my-project`.

  Returns:
    A list of (display_name, key_name) tuples in display order, where key_name
    is the API key resource name. Keys that are not provisioned on the project
    are omitted.

  Raises:
    apitools_exceptions.Error: If listing the project's API keys fails.
  """
  project = project_name.removeprefix('projects/')
  key_names = {}
  for key in apikeys.ListKeys(project):
    if key.displayName in MAPS_DEMO_API_KEY_DISPLAY_NAMES:
      key_names.setdefault(key.displayName, key.name)
  return [
      (display_name, key_names[display_name])
      for display_name in MAPS_DEMO_API_KEY_DISPLAY_NAMES
      if display_name in key_names
  ]


def _FormatError(error: apitools_exceptions.Error) -> str:
  """Formats an apitools error for display to the user."""
  if isinstance(error, apitools_exceptions.HttpError):
    return str(api_exceptions.HttpException(error))
  return str(error)


def PrintMapsDemoApiKeys(project_name: str) -> None:
  """Prints the Maps Platform demo API keys provisioned on a project, if any.

  The project is already provisioned at this point, so failing to retrieve the
  keys prints a status message with a command to retrieve them manually instead
  of failing the command. Each key string is retrieved independently, so one
  failure does not prevent the other keys from being printed.

  Args:
    project_name: The project resource name, e.g. `projects/my-project`.
  """
  try:
    keys = FindMapsDemoApiKeys(project_name)
  except apitools_exceptions.Error as e:
    project_id = project_name.removeprefix('projects/')
    log.status.Print(
        f'Unable to list the API keys for [{project_name}]:'
        f' {_FormatError(e)}\n'
        f'Run `gcloud services api-keys list --project={project_id}` to view'
        ' them.'
    )
    return
  if not keys:
    log.info(f'No Maps Platform demo API keys found for [{project_name}].')
    return
  for display_name, key_name in keys:
    try:
      key_string = apikeys.GetKeyString(key_name)
    except apitools_exceptions.Error as e:
      log.status.Print(
          f'Unable to retrieve [{display_name}]: {_FormatError(e)}\n'
          f'Run `gcloud services api-keys get-key-string {key_name}` to view'
          ' it.'
      )
      continue
    log.status.Print(f'{display_name}: {key_string}')
