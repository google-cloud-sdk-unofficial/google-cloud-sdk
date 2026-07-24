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
"""Common utilities for agentic_applications omnichannel_gateway commands."""

from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import properties


def GetApiEndpoint():
  """Returns the API endpoint host for agenticapplications API."""
  universal_domain = properties.VALUES.core.universe_domain.Get()
  use_mtls = properties.VALUES.context_aware.use_client_certificate.GetBool()
  if use_mtls:
    return f'agenticapplications.mtls.{universal_domain}'
  return f'agenticapplications.{universal_domain}'


def GetEndpointConfigsUrl(project, location, endpoint_config_id=None):
  """Returns the URL for omnichannelEndpointConfigs list or describe."""
  api_endpoint = GetApiEndpoint()
  url = f'https://{api_endpoint}/v1alpha/projects/{project}/locations/{location}/omnichannelEndpointConfigs'
  if endpoint_config_id:
    url = f'{url}/{endpoint_config_id}'
  return url


def GetRoutesUrl(project, location, route_id=None):
  """Returns the URL for routes list or describe."""
  api_endpoint = GetApiEndpoint()
  url = f'https://{api_endpoint}/v1alpha/projects/{project}/locations/{location}/omnichannelRoutes'
  if route_id:
    url = f'{url}/{route_id}'
  return url


def GetLocationResourceSpec(
    help_text='Location/Region of the omnichannel endpoint configurations.',
):
  return concepts.ResourceSpec(
      'agenticapplications.projects.locations',
      resource_name='location',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=concepts.ResourceParameterAttributeConfig(
          name='location',
          help_text=help_text,
      ),
  )


class OmnichannelOperationPoller(waiter.OperationPoller):
  """Custom poller for Omnichannel Gateway asynchronous operations."""

  def __init__(self, session, api_endpoint):
    self.session = session
    self.api_endpoint = api_endpoint

  def IsDone(self, operation):
    if operation.get('done', False):
      if 'error' in operation:
        raise core_exceptions.Error(
            f"Operation failed: {operation['error'].get('message')}"
        )
      return True
    return False

  def Poll(self, operation_ref):
    url = f'https://{self.api_endpoint}/v1alpha/{operation_ref}'
    try:
      response = self.session.get(url)
    except Exception as e:
      raise core_exceptions.Error(f'Failed to connect to API: {e}')
    if response.status_code != 200:
      raise core_exceptions.Error(
          f'Failed to check operation status (HTTP {response.status_code}): '
          f'{response.text}'
      )

    try:
      return response.json()
    except ValueError as exc:
      raise core_exceptions.Error(
          f'Invalid JSON response from server: {response.text}'
      ) from exc

  def GetResult(self, operation):
    return operation.get('response', operation)


def WaitForOperation(operation, session, message):
  """Waits for an omnichannel operation to complete.

  Args:
    operation: dict, the operation response.
    session: Authorized session.
    message: str, The message to show while waiting.

  Returns:
    The completed operation or resource.
  """
  api_endpoint = GetApiEndpoint()
  operation_ref = operation.get('name')
  if not operation_ref:
    return operation.get('response', operation)

  poller = OmnichannelOperationPoller(session, api_endpoint)
  return waiter.WaitFor(
      poller,
      operation_ref,
      message,
      max_wait_ms=300000,
  )
