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
"""Helper for get-version commands."""

import json
from typing import Any
from apitools.base.py import encoding
from googlecloudsdk.api_lib.compute.operations import poller
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import log


class GetVersionPoller(poller.Poller):
  """Custom poller for GetVersion that extracts metadata."""

  def GetResult(self, operation) -> Any:
    """Returns the metadata correctly extracted from an operation."""
    return operation.getVersionOperationMetadata or {}


def RunGetVersion(holder, args, host_ref, sbom_selections, association_str):
  """Runs the get-version command logic."""
  client = holder.client
  messages = client.messages

  # Call the method
  if not association_str:
    # Construct URL manually with a single slash
    base_url = client.apitools_client.url
    url = f'{base_url}projects/{host_ref.project}/zones/{host_ref.zone}/hosts/{host_ref.Name()}/getVersion?alt=json'

    # Convert enums to strings for JSON serialization
    selections = [str(selection) for selection in sbom_selections]
    body = {'sbomSelections': selections}

    response, content = client.apitools_client.http.request(
        url,
        method='POST',
        body=json.dumps(body),
        headers={'content-type': 'application/json'},
    )

    if response.status != 200:
      error_msg = (
          content.decode('utf-8') if isinstance(content, bytes) else content
      )
      raise exceptions.HttpException(
          f'HTTP Error {response.status}: {error_msg}'
      )

    operation = encoding.JsonToMessage(messages.Operation, content)
  else:
    request = messages.ComputeHostsGetVersionRequest(
        project=host_ref.project,
        zone=host_ref.zone,
        association=association_str,
        host=host_ref.Name(),
        hostsGetVersionRequest=messages.HostsGetVersionRequest(
            sbomSelections=sbom_selections
        ),
    )
    operation = client.apitools_client.hosts.GetVersion(request)

  # Wait for Operation
  operation_ref = holder.resources.Parse(
      operation.selfLink,
      collection='compute.zoneOperations',
  )

  if args.async_:
    log.status.Print(
        f'Get version operation in progress: [{operation_ref.SelfLink()}]'
    )
    return operation

  # Use custom poller
  operation_poller = GetVersionPoller(client.apitools_client.hosts)

  result = waiter.WaitFor(
      operation_poller,
      operation_ref,
      f'Getting version for host {host_ref.Name()} in progress.',
  )

  return result
