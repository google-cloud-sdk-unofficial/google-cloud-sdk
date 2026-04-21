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
from collections.abc import Iterable, Iterator
from typing import Any
from apitools.base.protorpclite import messages
from googlecloudsdk.api_lib.ai import util as ai_util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.ai import constants


# Fields to move from args to the policy object.
# Map of arg name (snake_case) to policy field name (camelCase).
_POLICY_FIELD_BY_ARG_NAME = {
    'display_name': 'displayName',
    'description': 'description',
    'natural_language_constraint': 'naturalLanguageConstraint',
    'agent': 'agent',
    'etag': 'etag',
}


def gateway_config_type(val: str) -> dict[str, str]:
  """Parses gateway-config flag value into a dictionary.

  The input format is a comma-separated string of key-value pairs.
  The 'name' key is required.

  Example input: 'name=GW,network=NET,subnetwork=SUBNET,dns-zone-name=DNS'

  Args:
    val: The flag value string to parse.

  Returns:
    A dictionary containing the parsed gateway configuration.
  """
  return arg_parsers.ArgDict(
      spec={
          'name': str,
          'network': str,
          'subnetwork': str,
          'dns-zone-name': str,
      },
      required_keys=['name'],
  )(val)


def mcp_tools_parser(val: str) -> messages.Message:
  """Parses mcp-tools flag value into a message object.

  The input format is a comma-separated string of key-value pairs.
  The 'mcp-server' key is required. The 'tools' key is optional and should
  be a semi-colon separated list of tool names.

  Example input: 'mcp-server=S1,tools=T1;T2'
  Example return: SemanticGovernancePolicyMcpTool(mcpServer='S1', tools=['T1',
  'T2'])

  Args:
    val: The flag value string to parse.

  Returns:
    A SemanticGovernancePolicyMcpTool message object.
  """
  mcp_tool_type = ai_util.GetMessage(
      'SemanticGovernancePolicyMcpTool', constants.BETA_VERSION
  )
  data: dict[str, Any] = arg_parsers.ArgDict(
      spec={'mcp-server': str, 'tools': str},
      required_keys=['mcp-server'],
  )(val)
  tools_val = data.get('tools')

  if tools_val:
    if isinstance(tools_val, list):
      tools_list = tools_val
    else:
      tools_list = [t.strip() for t in tools_val.split(';') if t.strip()]
  else:
    tools_list = []

  return mcp_tool_type(mcpServer=data.get('mcp-server'), tools=tools_list)


def get_version(unused_request: messages.Message) -> str:
  """Returns the API version based on the request message module.

  Args:
    unused_request: The request message object.

  Returns:
    The API version string (e.g., 'v1beta1').
  """
  del unused_request  # Unused
  return constants.BETA_VERSION


def get_semantic_governance_policy_field_name(
    request: messages.Message, version_id: str
) -> str | None:
  """Returns the name of the field in the request that holds the policy.

  Args:
    request: The request message object.
    version_id: The API version string.

  Returns:
    The name of the field (str) or None if not found.
  """
  if version_id == constants.BETA_VERSION:
    return 'googleCloudAiplatformV1beta1SemanticGovernancePolicy'

  if hasattr(request, 'semanticGovernancePolicy'):
    return 'semanticGovernancePolicy'

  return None


def _expand_mcp_tools(
    raw_mcp_tools: Iterable[messages.Message],
    mcp_tool_type: type[messages.Message],
) -> Iterator[messages.Message]:
  """Expands repeated tool entries so each server entry has exactly one tool.

  The Vertex AI Semantic Governance API requires that each entry in the
  mcpTools field contains exactly one tool. This function expands server
  entries with multiple tools into multiple server entries with one tool each.

  Args:
    raw_mcp_tools: List of unsanitized MCP tool message objects.
    mcp_tool_type: The message type class for MCP tools.

  Yields:
    Expanded MCP tool message objects, each with exactly one tool.
  """
  for server_entry in raw_mcp_tools:
    server = server_entry.mcpServer
    tools = getattr(server_entry, 'tools', [])
    if not tools:
      yield mcp_tool_type(mcpServer=server, tools=[])
    else:
      for tool in tools:
        yield mcp_tool_type(mcpServer=server, tools=[tool])


def set_semantic_governance_policy(
    ref: Any, args: argparse.Namespace, request: messages.Message
) -> messages.Message:
  """Sets the policy field in the request message.

  Args:
    ref: The internal reference.
    args: The parsed arguments.
    request: The request message to be modified.

  Returns:
    The modified request message.
  """
  del ref  # Unused
  version_id = get_version(request)

  field_name = get_semantic_governance_policy_field_name(request, version_id)
  if field_name is None:
    return request

  policy_type = ai_util.GetMessage('SemanticGovernancePolicy', version_id)
  if getattr(request, field_name) is None:
    # If policy doesn't exist, create an empty one.
    policy = policy_type()
    setattr(request, field_name, policy)
  else:
    policy = getattr(request, field_name)

  fields_to_update = []
  for arg_name, policy_field in _POLICY_FIELD_BY_ARG_NAME.items():
    if hasattr(args, arg_name) and args.IsSpecified(arg_name):
      value = getattr(args, arg_name)
      setattr(policy, policy_field, value)
      fields_to_update.append(policy_field)

  # The YAML declarative framework populates policy.mcpTools automatically.
  # We need to enforce the expansion rule: exactly one tool per server entry.
  if policy.mcpTools:
    mcp_tool_type = ai_util.GetMessage(
        'SemanticGovernancePolicyMcpTool', version_id
    )
    policy.mcpTools[:] = list(_expand_mcp_tools(policy.mcpTools, mcp_tool_type))

  if args.IsSpecified('mcp_tools'):
    fields_to_update.append('mcpTools')

  # Handle update_mask if it exists (for PATCH operations)
  if fields_to_update:
    mask_val = ','.join(sorted(fields_to_update))
    if hasattr(request, 'updateMask'):
      request.updateMask = mask_val
    elif hasattr(request, 'update_mask'):
      request.update_mask = mask_val

  return request


def set_delete_etag(
    ref: Any, args: argparse.Namespace, request: messages.Message
) -> messages.Message:
  """Sets the etag field in a delete request message.

  Args:
    ref: The resource reference.
    args: The parsed arguments.
    request: The request message to be modified.

  Returns:
    The modified request message.
  """
  del ref  # Unused
  if args.IsSpecified('etag'):
    request.etag = getattr(args, 'etag')
  return request


def set_engine_name(
    ref: Any, args: argparse.Namespace, request: messages.Message
) -> messages.Message:
  """Hook to set the name field for the singleton engine."""
  del ref  # Unused
  project = getattr(args, 'project', None)
  location = getattr(args, 'location', None)
  if project and location:
    request.name = f'projects/{project}/locations/{location}/semanticGovernancePolicyEngine'
  return request


def set_engine_update(
    ref: Any, args: argparse.Namespace, request: messages.Message
) -> messages.Message:
  """Hook to set the engine fields in an update request message."""
  del ref  # Unused
  version_id = get_version(request)
  fields_to_update = []

  # Set gateway_configs
  if hasattr(args, 'gateway_config') and args.IsSpecified('gateway_config'):
    gateway_config_val = getattr(args, 'gateway_config')
    gateway_name = gateway_config_val.get('name')

    gateway_config_msg_type = ai_util.GetMessage('GatewayConfig', version_id)

    config_kwargs = {}
    if 'network' in gateway_config_val:
      config_kwargs['network'] = gateway_config_val['network']
    if 'subnetwork' in gateway_config_val:
      config_kwargs['subnetwork'] = gateway_config_val['subnetwork']
    if 'dns-zone-name' in gateway_config_val:
      config_kwargs['dnsZoneName'] = gateway_config_val['dns-zone-name']

    gateway_config_msg = gateway_config_msg_type(**config_kwargs)

    engine_field = 'googleCloudAiplatformV1beta1SemanticGovernancePolicyEngine'
    # Fallback for GA if needed, but for now we assume v1beta1 based on the test
    if not hasattr(request, engine_field):
      engine_field = 'googleCloudAiplatformV1SemanticGovernancePolicyEngine'
    if not hasattr(request, engine_field):
      engine_field = 'semanticGovernancePolicyEngine'

    engine = getattr(request, engine_field)
    if engine is None:
      engine_type = ai_util.GetMessage(
          'SemanticGovernancePolicyEngine', version_id
      )
      engine = engine_type()
      setattr(request, engine_field, engine)

    gateway_configs_type = getattr(
        engine.__class__, 'GatewayConfigsValue', None
    )
    if gateway_configs_type:
      additional_property = gateway_configs_type.AdditionalProperty(
          key=gateway_name,
          value=gateway_config_msg,
      )
      engine.gatewayConfigs = gateway_configs_type(
          additionalProperties=[additional_property]
      )
    else:
      engine.gatewayConfigs = {gateway_name: gateway_config_msg}
    fields_to_update.append('gateway_configs')

  if fields_to_update:
    mask_val = ','.join(sorted(fields_to_update))
    if hasattr(request, 'update_mask'):
      request.update_mask = mask_val
    elif hasattr(request, 'updateMask'):
      request.updateMask = mask_val

  return request
