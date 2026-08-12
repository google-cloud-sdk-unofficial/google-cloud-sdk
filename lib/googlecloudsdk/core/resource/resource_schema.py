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

import sys

from apitools.base.protorpclite import messages
from googlecloudsdk.core import log


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
  has_page_token = any(
      f.name in ("nextPageToken", "next_page_token")
      for f in response_message_class.all_fields()
  )
  is_list_envelope = (
      class_name.startswith("List") and class_name.endswith("Response")
  ) or has_page_token

  if not is_list_envelope:
    return response_message_class

  candidates = []
  for field in response_message_class.all_fields():
    if getattr(field, "repeated", False):
      resource_cls = _ResolveFieldMessageType(field, response_message_class)
      if resource_cls:
        candidates.append((field, resource_cls))

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
