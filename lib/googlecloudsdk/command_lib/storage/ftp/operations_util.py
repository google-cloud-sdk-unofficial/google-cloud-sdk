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
"""Utilities for Cloud FTP long-running operations."""

from googlecloudsdk.api_lib.storage import ftp
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.core import resources


def GetOperationRef(operation_name):
  """Converts an operation resource name to a Resource ref."""
  return resources.REGISTRY.ParseRelativeName(
      operation_name, collection='ftp.projects.locations.operations'
  )


def WaitForOperation(
    operation_ref, message, result_service=None, max_wait_ms=3600000
):
  """Waits for a long-running operation to complete.

  Args:
    operation_ref: a Resource created by GetOperationRef describing the
      operation.
    message: the message to display to the user while waiting.
    result_service: apitools service for retrieving resulting resource. If None,
      assumes operation creates no resource (e.g. Delete).
    max_wait_ms: max wait in milliseconds.

  Returns:
    Resulting resource or None.
  """
  client = ftp.FtpClient()
  if result_service:
    poller = waiter.CloudOperationPoller(
        result_service, client.operations_service
    )
  else:
    poller = waiter.CloudOperationPollerNoResources(client.operations_service)

  return waiter.WaitFor(poller, operation_ref, message, max_wait_ms=max_wait_ms)
