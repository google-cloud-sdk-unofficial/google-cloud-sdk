# -*- coding: utf-8 -*- #
# Copyright 2024 Google LLC. All Rights Reserved.
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
"""Shared request hooks for the Dataplex surface."""

from __future__ import annotations

import argparse
import json

from typing import Any

from googlecloudsdk.calliope import exceptions
from googlecloudsdk.generated_clients.apis.dataplex.v1 import dataplex_v1_messages as messages


def TransformEntryRootPath(
    unused_ref: str,
    args: Any,
    request: (
        messages.DataplexProjectsLocationsLookupEntryRequest
        | messages.DataplexProjectsLocationsEntryGroupsEntriesGetRequest
    ),
):
  """Transforms the root path from the "." in CLI to empty string expected in API."""
  if args.paths is not None and isinstance(args.paths, list):
    request.paths = list(set(map(lambda p: p if p != '.' else '', args.paths)))
  return request


def TransformLookupContextOptionsToRequest(
    unused_ref: str,
    args: argparse.Namespace,
    request: messages.DataplexProjectsLocationsLookupContextRequest,
) -> messages.DataplexProjectsLocationsLookupContextRequest:
  """Constructs options map for LookupContext API request.

  This hook processes the --options and --context-format arguments
  to populate the 'options' field in the request body.

  Args:
    unused_ref: The resource reference, not used in this hook.
    args: The parsed arguments from the command line. Expected to have 'options'
      and 'context_format' attributes.
    request: The API request message to modify.

  Returns:
    The modified API request message.

  Raises:
    exceptions.InvalidArgumentException: If the --options argument is invalid,
      not a dictionary, or cannot be parsed as JSON.
  """
  if request.googleCloudDataplexV1LookupContextRequest is None:
    request.googleCloudDataplexV1LookupContextRequest = (
        messages.GoogleCloudDataplexV1LookupContextRequest()
    )
  body = request.googleCloudDataplexV1LookupContextRequest

  options_arg = getattr(args, 'options', None)

  if options_arg:
    try:
      parsed_options = json.loads(options_arg)
    except json.JSONDecodeError as e:
      raise exceptions.InvalidArgumentException(
          'options',
          f'Invalid JSON string for --options: {options_arg!r}. Details: {e!r}',
      ) from e

    if not isinstance(parsed_options, dict):
      raise exceptions.InvalidArgumentException(
          'options',
          '--options must result in a JSON object (dictionary), got type: '
          f'{type(parsed_options).__name__}'
      )
  else:
    parsed_options = {}

  context_format_arg = getattr(args, 'context_format', None)
  options_dict = {
      **parsed_options,
      **({'format': context_format_arg} if context_format_arg else {}),
  }

  final_options = {
      k: (json.dumps(v) if not isinstance(v, str) else v)
      for k, v in options_dict.items()
  }

  if final_options:
    body.options = messages.GoogleCloudDataplexV1LookupContextRequest.OptionsValue(
        additionalProperties=[
            messages.GoogleCloudDataplexV1LookupContextRequest.OptionsValue.AdditionalProperty(
                key=key,
                value=value,
            )
            for key, value in final_options.items()
        ]
    )
  return request
