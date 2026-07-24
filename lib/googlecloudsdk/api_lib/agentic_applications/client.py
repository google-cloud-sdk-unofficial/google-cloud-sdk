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
"""Client for interacting with Agentic Applications APIs."""

import json

from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core.credentials import requests as cred_requests


class OmnichannelGatewayClient(object):
  """Client for agenticapplications omnichannel gateway API."""

  def __init__(self, session=None):
    self.session = session or cred_requests.GetSession()

  def Request(self, method, url, body=None, params=None, error_msg=''):
    """Makes an HTTP request and parses the JSON response.

    Args:
      method: str, the HTTP method to use (e.g., 'GET', 'POST').
      url: str, the API URL.
      body: dict, optional payload to send as JSON.
      params: dict, optional query parameters.
      error_msg: str, message to prefix error with on failure.

    Returns:
      dict, the parsed JSON response.
    """
    kwargs = {}
    if params:
      kwargs['params'] = params

    if body is not None:
      kwargs['data'] = json.dumps(body)
      kwargs['headers'] = {'Content-Type': 'application/json'}

    try:
      response = self.session.request(method, url, **kwargs)
    except Exception as e:
      raise core_exceptions.Error(f'Failed to connect to API: {e}')

    if response.status_code not in (200, 201):
      raise core_exceptions.Error(
          f'{error_msg} (HTTP {response.status_code}): {response.text}'
      )

    try:
      return response.json()
    except ValueError as exc:
      raise core_exceptions.Error(
          f'Invalid JSON response from server: {response.text}'
      ) from exc
