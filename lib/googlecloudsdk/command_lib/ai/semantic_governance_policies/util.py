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
"""Utilities for Vertex AI semantic governance policies."""

import argparse
from typing import Any, Dict, Optional

from googlecloudsdk.api_lib.ai import util as ai_util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.ai import constants


# Fields to move from args to the policy object.
# Map of arg name (snake_case) to policy field name (snake_case).
_FIELDS_MAP = {
    'display_name': 'display_name',
    'description': 'description',
    'natural_language_constraint': 'natural_language_constraint',
    'agent': 'agent',
    'etag': 'etag',
}


def McpToolsType(value: str) -> Dict[str, str]:
  """Returns the type for the mcp-tools argument."""
  return arg_parsers.ArgDict(
      spec={
          'mcp-server': str,
          'tools': str,
      },
      required_keys=['mcp-server', 'tools'],
  )(value)


def GetVersion(request: Any):
  """Returns the API version based on the request message module."""
  module = request.__class__.__module__
  if 'v1beta1' in module:
    return constants.BETA_VERSION
  return constants.BETA_VERSION


def GetSemanticGovernancePolicyFieldName(
    request: Any, version_id: str
) -> Optional[str]:
  """Returns the name of the field in the request that holds the policy."""
  if version_id == constants.BETA_VERSION:
    field_name = 'google_cloud_aiplatform_v1beta1_semantic_governance_policy'
  elif version_id == constants.GA_VERSION:
    field_name = 'google_cloud_aiplatform_v1_semantic_governance_policy'
  else:
    # Fallback for other versions
    field_name = 'semantic_governance_policy'

  if hasattr(request, field_name):
    return field_name
  return None


def SetSemanticGovernancePolicy(
    ref: Any, args: argparse.Namespace, request: Any
) -> Any:
  """Hook to set the policy field in the request message."""
  del ref  # Unused
  version_id = GetVersion(request)

  field_name = GetSemanticGovernancePolicyFieldName(request, version_id)
  if field_name is None:
    return request

  policy_type = ai_util.GetMessage('SemanticGovernancePolicy', version_id)

  policy_kwargs = {}
  fields_to_update = []

  for arg_name, policy_field in _FIELDS_MAP.items():
    if hasattr(args, arg_name) and args.IsSpecified(arg_name):
      policy_kwargs[policy_field] = getattr(args, arg_name)
      fields_to_update.append(policy_field)

  policy = getattr(request, field_name)
  if policy is None:
    # If policy doesn't exist, create it with collected fields.
    policy = policy_type(**policy_kwargs)
    setattr(request, field_name, policy)
  else:
    # If policy exists (e.g., for update), apply the collected field updates.
    for field, value in policy_kwargs.items():
      setattr(policy, field, value)

  # The YAML declarative framework populates policy.mcp_tools automatically.
  # We just need to add it to the updateMask if specified.
  if hasattr(args, 'mcp_tools') and args.IsSpecified('mcp_tools'):
    fields_to_update.append('mcp_tools')

  # Handle update_mask if it exists (for PATCH operations)
  if hasattr(request, 'update_mask') and fields_to_update:
    request.update_mask = ','.join(sorted(fields_to_update))

  return request


def SetDeleteEtag(ref: Any, args: argparse.Namespace, request: Any) -> Any:
  """Hook to set the etag field in a delete request message."""
  del ref  # Unused
  if hasattr(args, 'etag') and args.IsSpecified('etag'):
    request.etag = getattr(args, 'etag')
  return request
