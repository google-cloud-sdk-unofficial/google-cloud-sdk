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
"""Resource schema introspection utilities for apitools messages.

This module provides static schema inspection for Google Cloud CLI commands by
analyzing underlying apitools / protorpclite Message response classes.
"""

import collections
import re
import sys

from apitools.base.protorpclite import messages
from googlecloudsdk.core import log
from googlecloudsdk.core.resource import resource_exceptions
from googlecloudsdk.core.resource import resource_lex
from googlecloudsdk.core.resource import resource_property
from googlecloudsdk.core.resource import resource_transform


# Common resource list collection field names (derived from Google AIP-132).
_STANDARD_COLLECTION_FIELD_NAMES = frozenset({
    "items",
    "resources",
    "data",
    "instances",
    "records",
    "results",
    "entries",
})

# Dynamic map types that allow arbitrary sub-keys at runtime.
_EXACT_DYNAMIC_TYPE_NAMES = frozenset({
    "struct",
    "value",
    "object",
    "json",
    "jsonobject",
    "jsonvalue",
    "any",
    "dictionary",
    "dict",
})

# Operator set and pre-compiled regex for inline bracket filter predicates.
_OPERATORS = frozenset({"=", ":", "!=", "~=", ">=", "<=", ">", "<"})
_FILTER_OPERATOR_RE = re.compile(r"!=|~=|>=|<=|=|<|>|:")

# Container transform names that preserve element schema traversal.
_CONTAINER_TRANSFORMS = frozenset({
    "map",
    "list",
    "sort",
    "slice",
    "filter",
    "notnull",
})


def _IsMessageClass(obj):
  """Returns True if obj is a valid protorpclite Message subclass.

  Args:
    obj: Object to inspect.

  Returns:
    bool: True if obj is a protorpclite Message subclass.
  """
  return isinstance(obj, type) and issubclass(obj, messages.Message)


def _ResolveFieldMessageType(field, parent_message_class):
  """Resolves a field's underlying Message subclass.

  Handles concrete Message types and string forward references
  (e.g. 'ChildMessage' or 'OuterMessage.InnerMessage').

  Args:
    field: An apitools Field descriptor object (e.g. MessageField).
    parent_message_class: The parent apitools Message class containing field.

  Returns:
    The resolved child Message subclass, or None if field type is scalar,
    unresolved, or invalid.
  """
  nested_type = getattr(field, "type", None)
  if isinstance(nested_type, str):
    type_name = nested_type
    parent_name = getattr(parent_message_class, "__name__", None)

    # Exact parent recursive reference match
    if parent_name and type_name == parent_name:
      return parent_message_class

    # Search roots: parent class (nested messages) and parent module (siblings)
    roots = [parent_message_class]
    module_name = getattr(parent_message_class, "__module__", None)
    if module_name and module_name in sys.modules:
      roots.append(sys.modules[module_name])

    for root in roots:
      curr = root
      for part in type_name.split("."):
        curr = getattr(curr, part, None)
        if not curr:
          break
      if _IsMessageClass(curr):
        return curr

    return None

  return nested_type if _IsMessageClass(nested_type) else None


def UnwrapResponseSchema(response_message_class, result_attribute=None):
  """Extracts underlying resource Message class from API response schema.

  For paginated list envelopes (e.g. ListInstancesResponse -> Instance),
  this utility extracts the repeated resource Message class. For non-envelope
  schemas, returns response_message_class unchanged.

  Args:
    response_message_class: The response Message class from an API method.
    result_attribute: Optional string attribute override from declarative
      command YAML specs (e.g., 'items' or 'items.instances').

  Returns:
    The repeated resource Message class if response_message_class is a List
    envelope; otherwise response_message_class unchanged.
  """
  if not _IsMessageClass(response_message_class):
    return response_message_class

  class_name = response_message_class.__name__
  has_page_token = False
  candidates = []
  for field in response_message_class.all_fields():
    if field.name in ("nextPageToken", "next_page_token"):
      has_page_token = True
    if getattr(field, "repeated", False):
      resource_cls = _ResolveFieldMessageType(field, response_message_class)
      if resource_cls:
        candidates.append((field, resource_cls))

  is_list_envelope = (
      class_name.startswith("List") and class_name.endswith("Response")
  ) or has_page_token

  if not (is_list_envelope or result_attribute):
    return response_message_class

  if not candidates:
    return response_message_class

  # Handle result_attribute override (e.g. 'items' or dot-path 'items.sub').
  if result_attribute:
    tokens = [t.lower() for t in str(result_attribute).split(".") if t]
    if tokens:
      top_token = tokens[0]
      matched_cls = None
      for field, resource_cls in candidates:
        if field.name.lower() == top_token:
          matched_cls = resource_cls
          break

      if matched_cls:
        curr_cls = matched_cls
        dot_path_failed = False
        for sub_token in tokens[1:]:
          if not _IsMessageClass(curr_cls) or not hasattr(
              curr_cls, "all_fields"
          ):
            dot_path_failed = True
            break
          next_cls = None
          for f in curr_cls.all_fields():
            if f.name.lower() == sub_token:
              next_cls = _ResolveFieldMessageType(f, curr_cls)
              break
          if next_cls:
            curr_cls = next_cls
          else:
            dot_path_failed = True
            break
        if not dot_path_failed:
          return curr_cls

      log.debug(
          "Specified result_attribute [%s] did not match any repeated message"
          " field in envelope [%s]. Falling back to standard collection"
          " search.",
          result_attribute,
          class_name,
      )

  if len(candidates) == 1:
    return candidates[0][1]

  # Check candidate fields against known AIP-132 standard collection names.
  standard_matches = [
      (field, resource_cls)
      for field, resource_cls in candidates
      if field.name.lower() in _STANDARD_COLLECTION_FIELD_NAMES
  ]

  if len(standard_matches) > 1:
    log.debug(
        "Ambiguous collection fields %s found in envelope [%s]. Returning [%s]"
        " as primary resource schema.",
        [f.name for f, _ in standard_matches],
        class_name,
        standard_matches[0][0].name,
    )

  if standard_matches:
    return standard_matches[0][1]

  if len(candidates) > 1:
    log.debug(
        "Non-standard ambiguous collection fields %s found in envelope [%s]."
        " Returning [%s] as primary resource schema.",
        [f.name for f, _ in candidates],
        class_name,
        candidates[0][0].name,
    )

  return candidates[0][1]


def _WalkSchemaBlocks(message_class):
  """Walks a Message class hierarchy breadth-first into named schema blocks.

  Deduplicates repeated message references so each distinct struct definition is
  yielded once.

  Args:
    message_class: The apitools Message class to walk.

  Yields:
    Tuple[str, List[str]]: Struct name and ordered list of formatted fields.
  """
  if not _IsMessageClass(message_class):
    return

  queue = collections.deque([message_class])
  visited_classes = set()
  # Tracks (class_name, field_tokens) tuples to deduplicate map structs.
  visited_signatures = set()

  while queue:
    current_class = queue.popleft()
    if current_class in visited_classes:
      continue
    visited_classes.add(current_class)

    fields_sorted = sorted(current_class.all_fields(), key=lambda f: f.name)
    field_tokens = []
    for field in fields_sorted:
      nested_class = _ResolveFieldMessageType(field, current_class)
      if nested_class:
        type_name = nested_class.__name__
        is_repeated = getattr(field, "repeated", False)
        formatted_type = f"[{type_name}]" if is_repeated else type_name
        field_tokens.append(f"{field.name}: {formatted_type}")
        if nested_class not in visited_classes:
          queue.append(nested_class)
      else:
        field_tokens.append(field.name)

    signature = (current_class.__name__, tuple(field_tokens))
    if signature in visited_signatures:
      continue
    visited_signatures.add(signature)

    yield current_class.__name__, field_tokens


def FormatNormalizedSchema(message_class):
  """Formats an apitools Message class into C-like multi-line schema text.

  Example:
    Instance {
      name
      networkInterfaces: [NetworkInterface]
      status
    }

    NetworkInterface {
      network
      networkIP
    }

  Args:
    message_class: The apitools Message class to format.

  Returns:
    str: Multi-line formatted schema string.
  """
  formatted_blocks = []
  for name, fields in _WalkSchemaBlocks(message_class):
    fields_str = "\n".join(f"  {f}" for f in fields)
    formatted_blocks.append(f"{name} {{\n{fields_str}\n}}")

  if formatted_blocks:
    return "\n\n".join(formatted_blocks)
  return ""


def GetCommandResponseSchema(command):
  """Resolves the primary resource Message response class for a gcloud command.

  Args:
    command: Calliope Command instance or CommandHelp wrapper object.

  Returns:
    The unwrapped resource Message subclass, or None if command is
    non-declarative or has response hooks / non-message response.
  """
  inner_cmd = getattr(command, "_command", command)
  yaml_spec = getattr(inner_cmd, "yaml_spec", None)
  if not yaml_spec:
    return None

  resp_spec = getattr(yaml_spec, "response", None)
  if not resp_spec:
    return None

  if getattr(resp_spec, "modify_response_hooks", None):
    return None

  methods = getattr(inner_cmd, "methods", [])
  method = (
      methods[0]
      if methods
      else getattr(inner_cmd, "operation_method", None)
  )
  if not method:
    return None

  try:
    response_cls = method.GetEffectiveResponseType()
  except (AttributeError, TypeError, KeyError, ValueError) as e:
    log.debug(
        "Failed to reflect response type for command [%s]: %s", command, e
    )
    return None

  result_attribute = getattr(resp_spec, "result_attribute", None)
  return UnwrapResponseSchema(response_cls, result_attribute=result_attribute)


def _IsDynamicOrMapType(message_type):
  """Returns True if message_type represents an untyped JSON object or map.

  Dynamic map fields (e.g. labels, metadata annotations, Struct/Any messages)
  allow arbitrary runtime sub-keys. Static validation stops traversing when a
  dynamic map field is reached.

  Example:
    _IsDynamicOrMapType(extra_types.JsonObject) -> True
    _IsDynamicOrMapType(Instance) -> False

  Args:
    message_type: The message type object or class to evaluate.

  Returns:
    True if message_type represents a dynamic map; False otherwise.
  """
  cls_name = getattr(message_type, "__name__", "")
  if cls_name.lower() in _EXACT_DYNAMIC_TYPE_NAMES:
    return True

  if _IsMessageClass(message_type):
    return (
        hasattr(message_type, "AdditionalProperty")
        or hasattr(message_type, "additionalProperties")
    )

  return False


def _TokenMatchesField(obj_or_cls, token):
  """Matches a key token against a dictionary or Protobuf message schema.

  Args:
    obj_or_cls: A dictionary, Protobuf Message instance, or Protobuf Message
      class to match against.
    token: String key attribute name to look up (supports snake_case and
      camelCase variations).

  Returns:
    (found, matching_field, next_type):
      found (bool): True if token matches a valid schema field or dict key;
        False otherwise.
      matching_field (messages.Field|None): The matching protorpclite Field
        descriptor when obj_or_cls is a Protobuf message; None if obj_or_cls is
        a dictionary or if found is False.
      next_type (type|object|None): The schema type or value for the next path
        step:
        - For Message classes: The child Protobuf Message class, or None if the
          field is a leaf scalar type (str, int, bool, enum).
        - For Message instances: The live attribute value (can be None).
        - For dictionaries: The value associated with token (can be None).
        - None if found is False.
  """
  # Fast path for dicts; reject primitives or None before Protobuf lookup
  if isinstance(obj_or_cls, dict):
    return (token in obj_or_cls, None, obj_or_cls.get(token))

  is_cls = isinstance(obj_or_cls, type)
  if not (is_cls or isinstance(obj_or_cls, messages.Message)):
    return False, None, None

  # Try exact O(1) Protobuf attribute match; fall back to case-insensitive scan
  try:
    field = obj_or_cls.field_by_name(token)
    field_name = token
  except KeyError:
    field = next(
        (
            f
            for f in obj_or_cls.all_fields()
            if resource_property.ConvertToSnakeCase(f.name) == token
            or resource_property.ConvertToCamelCase(f.name) == token
        ),
        None,
    )
    field_name = field.name if field else None

  if field is None:
    return False, None, None

  # In static mode return child Message class; in runtime mode fetch live value
  if is_cls:
    return True, field, _ResolveFieldMessageType(field, obj_or_cls)
  return True, field, getattr(obj_or_cls, field_name, None)


def _ValidateInlineFilterPredicate(current_type, token):
  """Validates inline bracket filter attributes against schema.

  Examples:
    _ValidateInlineFilterPredicate(Instance, 'status=RUNNING') -> True
    _ValidateInlineFilterPredicate(Instance, 'labels["env=prod"]') -> True

  Args:
    current_type: Current Protobuf message class or dict at this path point.
    token: The inline bracket filter string (e.g. 'status=RUNNING').

  Returns:
    bool: True if left-hand filter field attribute is valid in current_type.
  """
  raw_key = _FILTER_OPERATOR_RE.split(token)[0].strip().strip('"\'')
  target = current_type
  for p_seg in [s for s in raw_key.split(".") if s]:
    if isinstance(target, (list, tuple)) and target:
      target = target[0]
    found, _, target = _TokenMatchesField(target, p_seg)
    if not found:
      return False
  return True


def ValidateSingleKeyPath(response_type, key_str, known_symbols):
  """Validates a single projection key expression against response_type.

  Traverses key path tokens left-to-right against Protobuf field definitions.
  Accepts legal container transforms (.map(), .list()) and calliope format
  transforms (.date(), .lower()) when field resolution terminates or on leaf
  scalars.

  Examples:
    ValidateSingleKeyPath(InstanceMessage, 'net[0].ip', known) -> True
    ValidateSingleKeyPath(InstanceMessage, 'name[0]', known) -> False
    ValidateSingleKeyPath(InstanceMessage, 'invalidField', known) -> False

  Args:
    response_type: Protobuf Message class of the API response.
    key_str: Single projection key expression string or list of tokens.
    known_symbols: Set of allowed formatting transform names.

  Returns:
    bool: True if key_str is valid against response_type schema; False
      otherwise.
  """
  try:
    tokens = resource_lex.Lexer(str(key_str).replace("()", "")).Key()
  except resource_exceptions.Error:
    return False

  if not tokens:
    return False

  current_type = response_type
  last_field = None

  for token in tokens:
    # Array index or slice check (None = [])
    if token is None or isinstance(token, int):
      if not getattr(last_field, "repeated", False):
        return False
      continue

    # Inline bracket filter predicate check
    if isinstance(token, str) and any(op in token for op in _OPERATORS):
      if not _ValidateInlineFilterPredicate(current_type, token):
        return False
      continue

    # First check if token is a schema field on current_type
    found, matching_field, next_type = _TokenMatchesField(current_type, token)
    if found:
      last_field = matching_field
      if _IsDynamicOrMapType(next_type):
        return True
      current_type = next_type
      continue

    # If not a field, check if it is a Calliope formatting transform
    if isinstance(token, str) and token.lower() in known_symbols:
      if token.lower() not in _CONTAINER_TRANSFORMS:
        current_type = None
      continue

    return False

  return True


def ValidateReferencedKeys(
    command, referenced_keys, defaults=None
):
  """Validates referenced projection keys against command schema.

  Prints a non-fatal warning to log.status if any referenced key path is not
  found in the command's response schema.

  Examples:
    ValidateReferencedKeys(cmd, ['name', 'status', 'invalid_key'])
    # Output: Prints warning to log.status if any key is unrecognized.

  Args:
    command: Calliope command object.
    referenced_keys: Collection of projection key strings referenced in flags.
    defaults: Optional resource projection defaults object.
  """
  if isinstance(referenced_keys, str):
    referenced_keys = [referenced_keys]

  response_type = GetCommandResponseSchema(command)
  if not response_type or not referenced_keys:
    return

  known_symbols = set(resource_transform.GetTransforms())
  symbols = getattr(defaults, "symbols", None)
  if symbols:
    known_symbols.update(str(s).lower() for s in symbols)

  invalid_keys = []
  for key in referenced_keys:
    key_str = str(key or "").strip()
    if not key_str:
      continue
    if not ValidateSingleKeyPath(
        response_type, key_str, known_symbols=known_symbols
    ):
      invalid_keys.append(key_str)

  if invalid_keys:
    command_path = (
        " ".join(str(p) for p in command.GetPath() if p) if command else ""
    )
    log.status.Print(
        "WARNING: Projection key(s) [{0}] not recognized in resource schema"
        " for [{1}].\n\nTo view all available projection keys for this"
        " command, run:\n $ {1} --document=style=projections\n".format(
            ", ".join(invalid_keys), command_path
        )
    )

