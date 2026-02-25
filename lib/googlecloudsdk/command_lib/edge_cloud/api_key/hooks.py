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
"""Hooks for Edge Cloud API key surface."""

from googlecloudsdk.core import exceptions
from googlecloudsdk.generated_clients.apis.edgecontainer.v1alpha import edgecontainer_v1alpha_messages


def ConstructServiceAccountName(ref, args, request):
  """Constructs the full service account name from the ID and other context.

  Args:
    ref: The resource reference.
    args: The parsed command line arguments.
    request: The API request message.

  Raises:
    exceptions.RequiredArgumentException: If project or location is not
    provided.

  Returns:
    The modified request object with `apiKey.serviceAccountName` populated.
  """
  if args.IsSpecified('service_account'):
    project = args.project
    location = args.location
    sa_id = args.service_account

    if not project:
      # This should be caught by the resource argument's own validation
      raise exceptions.RequiredArgumentException(
          '--project', 'The --project flag is required.'
      )

    if not location:
      # This should be caught by the resource argument's own validation
      raise exceptions.RequiredArgumentException(
          '--location', 'The --location flag is required.'
      )

    service_account_name = (
        f'projects/{project}/locations/{location}/serviceAccounts/{sa_id}'
    )

    api_key_message_cls = edgecontainer_v1alpha_messages.ApiKey

    if not hasattr(request, 'apiKey') or request.apiKey is None:
      # Instantiate the message type for ApiKey
      request.apiKey = api_key_message_cls()

    request.apiKey.serviceAccountName = service_account_name

    # The 'service-account' argument is only used in this hook to construct
    # the serviceAccountName. It's not a direct field in the API request.
    delattr(args, 'service_account')

  return request
