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
"""Utility for Data Lineage commands."""

from typing import Any
from apitools.base.py import base_api
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import properties


def GetClient() -> base_api.BaseApiClient:
  """Returns the API client for the datalineage v1 service."""
  return apis.GetClientInstance('datalineage', 'v1')


def GetMessages() -> Any:
  """Returns the messages module for the datalineage v1 service."""
  return apis.GetMessagesModule('datalineage', 'v1')


def GetConfigResourceName(args: Any) -> str:
  """Constructs the full config resource name based on parent flags.

  Args:
    args: An object containing parsed command line arguments. Expected to have
      attributes 'project', 'folder', and 'organization'.

  Returns:
    A string representing the full resource name for the Data Lineage config,
    in the format 'projects/{project}/locations/global/config',
    'folders/{folder}/locations/global/config', or
    'organizations/{organization}/locations/global/config'.
  """
  if not (args.project or args.folder or args.organization):
    # Default to current project if none specified.
    project = properties.VALUES.core.project.GetOrFail()
    return f'projects/{project}/locations/global/config'

  if args.project:
    return f'projects/{args.project}/locations/global/config'
  elif args.folder:
    return f'folders/{args.folder}/locations/global/config'
  else:
    return f'organizations/{args.organization}/locations/global/config'
