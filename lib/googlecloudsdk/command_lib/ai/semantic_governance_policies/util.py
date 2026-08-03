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
import re
from typing import Any
from apitools.base.protorpclite import messages
from googlecloudsdk.api_lib.ai import util as ai_util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources

# Locations that should be served from the global aiplatform endpoint
# (i.e., not prefixed with the region in the hostname).
_GLOBAL_LOCATIONS = frozenset(["global"])


def set_regional_endpoint(
    ref: resources.Resource | None,
    args: argparse.Namespace,
    request: messages.Message,
) -> messages.Message:
  """Overrides the aiplatform endpoint with the regional endpoint.

  Vertex AI requires that requests for regional resources be sent to the
  matching regional endpoint (e.g.,
  ``https://us-central1-aiplatform.<universe-domain>/``) rather than the
  default global endpoint. Without this override, the API rejects the
  request with ``The provided location ID doesn't match the endpoint.''

  This is registered as a `modify_request_hooks` entry in the YAML command
  spec so that it runs after argument parsing but before the apitools client
  is constructed inside `method.Call`. The override is set on the
  `api_endpoint_overrides.aiplatform` property, which is read by
  `apis.GetClientInstance` when the client is built.

  Args:
    ref: The parsed primary resource reference. For most semantic governance
      policy commands, this carries the `locationsId` attribute. May be `None`
      for commands that don't have a primary resource reference.
    args: The parsed command-line arguments. Used as a fallback source for the
      location when `ref` does not carry it.
    request: The request message to be sent. Returned unmodified.

  Returns:
    The request message, unchanged.
  """
  if ref is not None and hasattr(ref, "locationsId"):
    location = getattr(ref, "locationsId")
  elif hasattr(args, "location"):
    location = getattr(args, "location")
  else:
    location = None

  if not location or location in _GLOBAL_LOCATIONS:
    return request
  version_id = get_version(request)
  endpoint = endpoint_util.GetEffectiveEndpoint(
      version=version_id, region=location
  )
  log.status.Print("Using endpoint [{}]".format(endpoint))
  properties.VALUES.api_endpoint_overrides.aiplatform.Set(endpoint)
  return request


# Fields to move from args to the policy object.
# Map of arg name (snake_case) to policy field name (camelCase).
_POLICY_FIELD_BY_ARG_NAME = {
    "display_name": "displayName",
    "description": "description",
    "natural_language_constraint": "naturalLanguageConstraint",
    "agent": "agent",
    "etag": "etag",
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
          "name": str,
          "network": str,
          "subnetwork": str,
          "dns-zone-name": str,
      },
      required_keys=["name"],
  )(val)


def mcp_tools_parser(val: str) -> dict[str, Any]:
  """Parses mcp-tools flag value into a dictionary.

  The input format is a comma-separated string of key-value pairs.
  The 'mcp-server' key is required. The 'tools' key is optional and should
  be a semi-colon separated list of tool names.

  Returns a plain dict so that set_semantic_governance_policy can convert it
  into the correct versioned message type at request time.

  Example input: 'mcp-server=S1,tools=T1;T2'
  Example return: {'mcpServer': 'S1', 'tools': ['T1', 'T2']}

  Args:
    val: The flag value string to parse.

  Returns:
    A dict with 'mcpServer' and 'tools' keys.
  """
  data: dict[str, Any] = arg_parsers.ArgDict(
      spec={"mcp-server": str, "tools": str},
      required_keys=["mcp-server"],
  )(val)
  tools_val = data.get("tools")

  if tools_val:
    if isinstance(tools_val, list):
      tools_list = tools_val
    else:
      tools_list = [t.strip() for t in tools_val.split(";") if t.strip()]
  else:
    tools_list = []

  return {"mcpServer": data.get("mcp-server"), "tools": tools_list}


def get_version(request: messages.Message) -> str:
  """Returns the API version based on the request message module.

  Args:
    request: The request message object.

  Returns:
    The API version string (e.g., 'v1' or 'v1beta1').
  """
  module = type(request).__module__
  if "v1beta1" in module:
    return constants.BETA_VERSION
  return constants.GA_VERSION


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
    return "googleCloudAiplatformV1beta1SemanticGovernancePolicy"

  if version_id == constants.GA_VERSION:
    return "googleCloudAiplatformV1SemanticGovernancePolicy"

  if hasattr(request, "semanticGovernancePolicy"):
    return "semanticGovernancePolicy"

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
    if isinstance(server_entry, dict):
      server = server_entry.get("mcpServer")
      tools = server_entry.get("tools", [])
    else:
      server = server_entry.mcpServer
      tools = getattr(server_entry, "tools", [])
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

  policy_type = ai_util.GetMessage("SemanticGovernancePolicy", version_id)
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

  # Handle mcp-tools. `mcp_tools_parser` returns plain dicts (it can't build
  # the versioned message type without knowing the API version), so we read
  # `args.mcp_tools` here and convert each entry to the correct versioned
  # `SemanticGovernancePolicyMcpTool` message. We also expand any multi-tool
  # entries into one tool per entry, which the API requires. This overrides
  # anything the declarative framework placed on `policy.mcpTools` via the
  # BETA `api_field` binding (harmless: the result is identical) and is the
  # sole population path for the GA track, whose `issue_request_hook` builds
  # the request from scratch.
  if args.IsSpecified("mcp_tools"):
    mcp_tool_type = ai_util.GetMessage(
        "SemanticGovernancePolicyMcpTool", version_id
    )
    raw_tools = getattr(args, "mcp_tools", []) or []
    policy.mcpTools = list(_expand_mcp_tools(raw_tools, mcp_tool_type))
    fields_to_update.append("mcpTools")

  # Handle update_mask if it exists (for PATCH operations)
  if fields_to_update:
    mask_val = ",".join(sorted(fields_to_update))
    if hasattr(request, "updateMask"):
      request.updateMask = mask_val
    elif hasattr(request, "update_mask"):
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
  if args.IsSpecified("etag"):
    request.etag = getattr(args, "etag")
  return request


def set_engine_name(
    ref: Any, args: argparse.Namespace, request: messages.Message
) -> messages.Message:
  """Hook to set the name field for the singleton engine."""
  del ref  # Unused
  project = getattr(args, "project", None)
  location = getattr(args, "location", None)
  if project and location:
    request.name = f"projects/{project}/locations/{location}/semanticGovernancePolicyEngine"
  return request


# Matches an LRO name of the form
# projects/{project}/locations/{location}/semanticGovernancePolicies/{policy}/operations/{op}
_NESTED_LRO_NAME_RE = re.compile(
    r"^(projects/[^/]+/locations/[^/]+)/semanticGovernancePolicies/[^/]+/operations/([^/]+)$"
)


def _normalize_lro_name(name: str) -> str:
  """Rewrites a nested SGP LRO name to the top-level operations form.

  gcloud parses returned operation names against a collection registered in
  ``resources.py``. The aiplatform v1 discovery doc has never exposed the
  ``projects.locations.semanticGovernancePolicies.operations`` sub-collection
  (see b/524667335): the ``doc.yaml`` override in
  ``//google/cloud/aiplatform`` strips the parent-scoped
  ``google.longrunning.Operations.*`` HTTP bindings from the public v1
  discovery.

  The v1 server still stamps LRO names under the policy resource, but it also
  accepts the top-level ``projects/{p}/locations/{l}/operations/{op}`` URL
  for GET. This helper rewrites the returned name so that gcloud can parse it
  against ``aiplatform.projects.locations.operations`` (which does exist in
  v1) and poll via the top-level Get.

  If the name doesn't match the nested pattern, it is returned unchanged (so
  BETA calls, which return names that parse against the nested collection
  that DOES exist in v1beta1, are unaffected).

  Args:
    name: The operation name returned by the server.

  Returns:
    The (possibly rewritten) operation name.
  """
  match = _NESTED_LRO_NAME_RE.match(name)
  if not match:
    return name
  return f"{match.group(1)}/operations/{match.group(2)}"


def _issue_and_normalize_lro(
    ref: resources.Resource | None,
    args: argparse.Namespace,
    method_name: str,
) -> messages.Message:
  """Executes the underlying create/patch/delete and normalizes the LRO name.

  This is used as a YAML ``issue_request_hook`` for the aiplatform v1 GA SGP
  surfaces to work around the missing nested operations collection in the
  v1 discovery doc (see :func:`_normalize_lro_name`).

  The hook re-runs the standard request-building pipeline (equivalent to what
  ``yaml_command_translator._CommonRun`` would do) and then rewrites the
  returned operation's ``name`` field from the nested form to the top-level
  form so gcloud's async polling machinery can find a matching collection.

  Args:
    ref: The parsed primary resource reference.
    args: The parsed command-line arguments.
    method_name: The apitools method name to invoke on
      ``client.projects_locations_semanticGovernancePolicies`` (one of
      ``Create``, ``Patch``, ``Delete``).

  Returns:
    The API response, with ``name`` normalized if it was a nested LRO name.
  """
  version_id = constants.GA_VERSION
  api_version = constants.AI_PLATFORM_API_VERSION[version_id]
  msgs = apis.GetMessagesModule("aiplatform", api_version)

  # The primary resource ref (``ref``) provides the projects/location/policy
  # ids in a form that already matches what the underlying framework parsed
  # from the command line. Reading from ``args`` directly is not reliable in
  # tests (``args.project`` may be ``None`` even when a project is specified
  # via the resource concept).
  ref_dict = ref.AsDict() if ref is not None else {}
  project = ref_dict.get("projectsId")
  location = ref_dict.get("locationsId")
  policy_id = ref_dict.get("semanticGovernancePoliciesId")
  parent = f"projects/{project}/locations/{location}"
  policy_name = f"{parent}/semanticGovernancePolicies/{policy_id}"

  if method_name == "Create":
    request = (
        msgs.AiplatformProjectsLocationsSemanticGovernancePoliciesCreateRequest(
            parent=parent,
            semanticGovernancePolicyId=policy_id,
        )
    )
  elif method_name == "Patch":
    request = (
        msgs.AiplatformProjectsLocationsSemanticGovernancePoliciesPatchRequest(
            name=policy_name,
        )
    )
  elif method_name == "Delete":
    request = (
        msgs.AiplatformProjectsLocationsSemanticGovernancePoliciesDeleteRequest(
            name=policy_name,
        )
    )
  else:
    raise ValueError(f"Unsupported method for GA LRO hook: {method_name}")

  # Apply the same modify_request_hooks that the YAML declares for BETA. This
  # keeps request construction identical between tracks.
  request = set_regional_endpoint(ref, args, request)
  if method_name in ("Create", "Patch"):
    request = set_semantic_governance_policy(ref, args, request)
  if method_name == "Delete":
    request = set_delete_etag(ref, args, request)

  # Build the client after set_regional_endpoint may have set a regional
  # override so the actual call goes to the correct endpoint.
  client = apis.GetClientInstance("aiplatform", api_version)
  service = client.projects_locations_semanticGovernancePolicies
  response = getattr(service, method_name)(request)

  # Normalize the returned LRO name so the async machinery can parse it
  # against ``aiplatform.projects.locations.operations`` (see
  # :func:`_normalize_lro_name`).
  if hasattr(response, "name") and isinstance(response.name, str):
    response.name = _normalize_lro_name(response.name)
  return response


def issue_create_and_normalize_lro(
    ref: resources.Resource | None, args: argparse.Namespace
) -> messages.Message:
  """``issue_request_hook`` for GA ``create``."""
  return _issue_and_normalize_lro(ref, args, "Create")


def issue_patch_and_normalize_lro(
    ref: resources.Resource | None, args: argparse.Namespace
) -> messages.Message:
  """``issue_request_hook`` for GA ``update`` (HTTP PATCH)."""
  return _issue_and_normalize_lro(ref, args, "Patch")


def issue_delete_and_normalize_lro(
    ref: resources.Resource | None, args: argparse.Namespace
) -> messages.Message:
  """``issue_request_hook`` for GA ``delete``."""
  return _issue_and_normalize_lro(ref, args, "Delete")


def set_engine_update(
    ref: Any, args: argparse.Namespace, request: messages.Message
) -> messages.Message:
  """Hook to set the engine fields in an update request message."""
  del ref  # Unused
  version_id = get_version(request)
  fields_to_update = []

  # Set gateway_configs
  if hasattr(args, "gateway_config") and args.IsSpecified("gateway_config"):
    gateway_config_val = getattr(args, "gateway_config")
    gateway_name = gateway_config_val.get("name")

    gateway_config_msg_type = ai_util.GetMessage("GatewayConfig", version_id)

    config_kwargs = {}
    if "network" in gateway_config_val:
      config_kwargs["network"] = gateway_config_val["network"]
    if "subnetwork" in gateway_config_val:
      config_kwargs["subnetwork"] = gateway_config_val["subnetwork"]
    if "dns-zone-name" in gateway_config_val:
      config_kwargs["dnsZoneName"] = gateway_config_val["dns-zone-name"]

    gateway_config_msg = gateway_config_msg_type(**config_kwargs)

    engine_field = "googleCloudAiplatformV1beta1SemanticGovernancePolicyEngine"
    # Fallback for GA if needed, but for now we assume v1beta1 based on the test
    if not hasattr(request, engine_field):
      engine_field = "googleCloudAiplatformV1SemanticGovernancePolicyEngine"
    if not hasattr(request, engine_field):
      engine_field = "semanticGovernancePolicyEngine"

    engine = getattr(request, engine_field)
    if engine is None:
      engine_type = ai_util.GetMessage(
          "SemanticGovernancePolicyEngine", version_id
      )
      engine = engine_type()
      setattr(request, engine_field, engine)

    gateway_configs_type = getattr(
        engine.__class__, "GatewayConfigsValue", None
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
    fields_to_update.append("gatewayConfigs")

  if fields_to_update:
    mask_val = ",".join(sorted(fields_to_update))
    if hasattr(request, "update_mask"):
      request.update_mask = mask_val
    elif hasattr(request, "updateMask"):
      request.updateMask = mask_val

  return request
