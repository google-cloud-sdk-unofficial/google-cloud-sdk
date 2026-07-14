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
"""Hooks for ApiHub commands."""

import json
import re

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import files as file_utils

# Valid HTTP methods for McpToolConfig.http_operation.method. Must match
# the values of GoogleCloudApihubV1HttpOperationConfig.MethodValueValuesEnum
# (generated from the HttpOperation.Method enum in
# //google/cloud/apihub/v1main/common_fields.proto, which the proto field
# OperationConfig.HttpOperationConfig.method imports), excluding the
# METHOD_UNSPECIFIED sentinel which is invalid as user input.
_VALID_HTTP_METHODS = frozenset(
    ["GET", "PUT", "POST", "DELETE", "OPTIONS", "HEAD", "PATCH", "TRACE"]
)

_VALID_TOOLS_FILE_EXTENSIONS = (".yaml", ".yml", ".json")


def _BuildMcpToolConfig(messages, tool_dict, index):
  """Builds a single McpToolConfig proto from a parsed dict.

  Args:
    messages: The apihub_v1_messages module.
    tool_dict: A dict from the parsed --mcp-tools-from-file entry. Keys may use
      snake_case (`tool_id`) or kebab-case (`tool-id`).
    index: Positional index of this entry in the file (for error messages).

  Returns:
    A GoogleCloudApihubV1McpToolConfig proto.

  Raises:
    calliope_exceptions.InvalidArgumentException: if the dict is malformed.
  """
  tool_id = tool_dict.get("tool_id") or tool_dict.get("tool-id")
  if not tool_id:
    raise calliope_exceptions.InvalidArgumentException(
        "--mcp-tools-from-file",
        "Tool at index {} is missing required field 'tool_id'.".format(index),
    )

  description = tool_dict.get("description")
  if not description:
    raise calliope_exceptions.InvalidArgumentException(
        "--mcp-tools-from-file",
        "Tool '{}' is missing required field 'description'.".format(tool_id),
    )

  has_op_name = isinstance(tool_dict.get("operation"), str)
  has_http_op = isinstance(tool_dict.get("http_operation"), dict)
  if has_op_name and has_http_op:
    raise calliope_exceptions.InvalidArgumentException(
        "--mcp-tools-from-file",
        "Tool '{}' specifies both 'operation' and 'http_operation'; "
        "provide exactly one.".format(tool_id),
    )
  if not (has_op_name or has_http_op):
    raise calliope_exceptions.InvalidArgumentException(
        "--mcp-tools-from-file",
        "Tool '{}' must specify exactly one of 'operation' (resource name) "
        "or 'http_operation' (spec/path/method).".format(tool_id),
    )

  op_cfg = messages.GoogleCloudApihubV1OperationConfig()
  if has_op_name:
    op_cfg.operation = tool_dict["operation"]
  else:
    http_op = tool_dict["http_operation"]
    for required_key in ("spec", "path", "method"):
      if required_key not in http_op:
        raise calliope_exceptions.InvalidArgumentException(
            "--mcp-tools-from-file",
            "Tool '{}' http_operation is missing required field '{}'.".format(
                tool_id, required_key
            ),
        )
    method_str = str(http_op["method"]).upper()
    if method_str not in _VALID_HTTP_METHODS:
      raise calliope_exceptions.InvalidArgumentException(
          "--mcp-tools-from-file",
          "Invalid HTTP method '{}' for tool '{}'. Valid values: {}.".format(
              http_op["method"], tool_id, ", ".join(sorted(_VALID_HTTP_METHODS))
          ),
      )
    method_enum_cls = (
        messages.GoogleCloudApihubV1HttpOperationConfig.MethodValueValuesEnum
    )
    op_cfg.httpOperation = messages.GoogleCloudApihubV1HttpOperationConfig(
        spec=http_op["spec"],
        path=http_op["path"],
        method=method_enum_cls.lookup_by_name(method_str),
    )

  return messages.GoogleCloudApihubV1McpToolConfig(
      toolId=tool_id, description=description, operation=op_cfg
  )


def ProcessMcpToolsFromFile(unused_ref, args, request):
  """Modify-request hook for `servers configure-and-deploy`.

  When --mcp-tools-from-file is provided, parses the YAML/JSON file and
  populates request.mcpServerConfig.tools with the resulting
  McpToolConfig protos. Validates required fields, the oneof identifier on
  each tool's operation, the HTTP method enum, file extension, and
  tool_id uniqueness.

  When --mcp-tools is used instead, the declarative arg_dict in the
  partial already populates request.mcpServerConfig.tools; this hook is
  a no-op in that case.

  Args:
    unused_ref: Resource reference (unused).
    args: Parsed argparse namespace.
    request: The request message being built.

  Returns:
    The modified request.

  Raises:
    calliope_exceptions.InvalidArgumentException: on validation failure.
  """
  file_path = getattr(args, "mcp_tools_from_file", None)
  if not file_path:
    return request

  if not file_path.endswith(_VALID_TOOLS_FILE_EXTENSIONS):
    raise calliope_exceptions.InvalidArgumentException(
        "--mcp-tools-from-file",
        "--mcp-tools-from-file expects a .yaml, .yml, or .json extension; "
        "got: {}".format(file_path),
    )

  try:
    if file_path.endswith(".json"):
      raw = file_utils.ReadFileContents(file_path)
      parsed = json.loads(raw)
    else:
      parsed = yaml.load_path(file_path)
  except (ValueError, yaml.Error, file_utils.Error) as exc:
    raise calliope_exceptions.InvalidArgumentException(
        "--mcp-tools-from-file",
        "Failed to parse {}: {}".format(file_path, exc),
    )

  if not isinstance(parsed, list):
    raise calliope_exceptions.InvalidArgumentException(
        "--mcp-tools-from-file",
        "--mcp-tools-from-file must contain a list at top level; got: {}."
        .format(type(parsed).__name__),
    )

  messages = apis.GetMessagesModule("apihub", "v1")
  seen_ids = set()
  tools = []
  for idx, tool_dict in enumerate(parsed):
    if not isinstance(tool_dict, dict):
      raise calliope_exceptions.InvalidArgumentException(
          "--mcp-tools-from-file",
          "Tool at index {} must be a dict; got: {}.".format(
              idx, type(tool_dict).__name__
          ),
      )
    tool = _BuildMcpToolConfig(messages, tool_dict, idx)
    if tool.toolId in seen_ids:
      raise calliope_exceptions.InvalidArgumentException(
          "--mcp-tools-from-file",
          "Duplicate tool_id '{}'; tool_id must be unique across all "
          "tools.".format(tool.toolId),
      )
    seen_ids.add(tool.toolId)
    tools.append(tool)

  # The request object here is the gcloud-generated request wrapper
  # (ApihubProjectsLocationsConfigureAndDeployServerRequest), which embeds
  # the actual request body as
  # googleCloudApihubV1ConfigureAndDeployServerRequest.
  body = request.googleCloudApihubV1ConfigureAndDeployServerRequest
  if body is None:
    body = messages.GoogleCloudApihubV1ConfigureAndDeployServerRequest()
    request.googleCloudApihubV1ConfigureAndDeployServerRequest = body
  if body.mcpServerConfig is None:
    body.mcpServerConfig = messages.GoogleCloudApihubV1McpServerConfig()
  # The mutex group in the partial guarantees this branch is only entered
  # when --mcp-tools is not set, so we can overwrite tools without losing
  # flag-set values.
  body.mcpServerConfig.tools = tools

  return request


_SYSTEM_ATTRIBUTE_SUFFIXES = [
    "enum_values",
    "enumValues",
    "string_values",
    "stringValues",
    "json_values",
    "jsonValues",
    "uri_values",
    "uriValues",
]


def _CamelCase(snake_str):
  """Converts a snake_case string to camelCase, handling dots."""
  parts = snake_str.split(".")
  camel_parts = []
  for part in parts:
    camel_parts.append(re.sub(r"_([a-z])", lambda x: x.group(1).upper(), part))
  return ".".join(camel_parts)


def _AddConfigEntries(config, snake_field, suffixes, target=None):
  """Adds config entries for a field, handling snake_case and camelCase.

  Args:
    config: The dictionary to add entries to.
    snake_field: The field name in snake_case.
    suffixes: A list of suffixes for this field.
    target: The top-level field name in the update mask. Defaults to
      snake_field.
  """
  if target is None:
    target = snake_field
  camel_field = _CamelCase(snake_field)

  for suffix in suffixes:
    config[f"{snake_field}.{suffix}"] = target
    if snake_field != camel_field:
      config[f"{camel_field}.{suffix}"] = target


def _AddSystemAttributeConfigEntries(config, *snake_fields):
  for field in snake_fields:
    _AddConfigEntries(config, field, _SYSTEM_ATTRIBUTE_SUFFIXES)


def ModifyUpdateMask(ref, unused_args, request):
  """Modifies the update mask to use top-level fields for complex attributes.

  Args:
    ref: The resource reference.
    unused_args: The parsed command arguments.
    request: The request message.

  Returns:
    The modified request.
  """
  if not request.updateMask:
    return request

  # API Collection Config
  # Collection: apihub.projects.locations.apis
  api_field_config = {}
  _AddSystemAttributeConfigEntries(
      api_field_config,
      "team",
      "target_user",
      "business_unit",
      "maturity_level",
      "api_style",
      "api_requirements",
      "api_functional_requirements",
      "api_technical_requirements",
  )
  _AddConfigEntries(
      api_field_config, "owner", ["email", "display_name", "displayName"]
  )
  _AddConfigEntries(
      api_field_config, "documentation", ["external_uri", "externalUri"]
  )

  # Version Collection Config
  # Collection: apihub.projects.locations.apis.versions
  version_field_config = {}
  _AddSystemAttributeConfigEntries(
      version_field_config, "lifecycle", "compliance", "accreditation"
  )
  _AddConfigEntries(
      version_field_config, "documentation", ["external_uri", "externalUri"]
  )

  # Operation Collection Config
  # Collection: apihub.projects.locations.apis.versions.operations
  operation_field_config = {}
  _AddConfigEntries(
      operation_field_config,
      "details.documentation",
      ["external_uri", "externalUri"],
  )
  _AddConfigEntries(
      operation_field_config,
      "details.http_operation.path",
      ["description", "path"],
  )
  _AddConfigEntries(
      operation_field_config, "details.http_operation.method", ["method"]
  )

  # Spec Collection Config
  # Collection: apihub.projects.locations.apis.versions.specs
  spec_field_config = {}
  _AddSystemAttributeConfigEntries(spec_field_config, "spec_type")
  _AddConfigEntries(
      spec_field_config, "documentation", ["external_uri", "externalUri"]
  )
  _AddConfigEntries(
      spec_field_config, "contents", ["mime_type", "mimeType", "contents"]
  )

  # Deployment Collection Config
  # Collection: apihub.projects.locations.deployments
  deployment_field_config = {}
  _AddSystemAttributeConfigEntries(
      deployment_field_config,
      "deployment_type",
      "slo",
      "environment",
      "management_url",
      "source_uri",
  )
  _AddConfigEntries(
      deployment_field_config, "documentation", ["external_uri", "externalUri"]
  )

  # Select config based on collection
  collection = ref.Collection()
  config_map = {
      "apihub.projects.locations.apis": api_field_config,
      "apihub.projects.locations.apis.versions": version_field_config,
      "apihub.projects.locations.apis.versions.specs": spec_field_config,
      "apihub.projects.locations.deployments": deployment_field_config,
      "apihub.projects.locations.apis.versions.operations": (
          operation_field_config
      ),
  }
  mask_replacements = config_map.get(collection, {})

  new_mask_paths = []
  raw_paths = request.updateMask.split(",")

  for path in raw_paths:
    path = path.strip()
    # Check if this path needs to be replaced
    replaced = False
    for granulated, top_level in mask_replacements.items():
      # Handle both exact match and sub-field match
      if path == granulated or path.startswith(granulated + "."):
        if top_level not in new_mask_paths:
          new_mask_paths.append(top_level)
        replaced = True
        break

    if not replaced:
      new_mask_paths.append(path)

  # Remove duplicates and join
  new_mask_paths = sorted(list(set(new_mask_paths)))
  request.updateMask = ",".join(new_mask_paths)

  return request
