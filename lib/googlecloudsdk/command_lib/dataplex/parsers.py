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
"""Utilities for Dataplex Entries commands."""

from __future__ import annotations

import datetime
import json
from typing import Any, List

from googlecloudsdk.api_lib.dataplex import util as dataplex_util
from googlecloudsdk.api_lib.util import messages as messages_util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import yaml
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import files

dataplex_message = dataplex_util.GetMessageModule()

_BatchChange = (
    dataplex_message.GoogleCloudDataplexV1BatchChangeMetadataRequestChange
)
# The fields of the `oneof payload` of a batch change, exactly one of which must
# be set. The generated message doesn't expose the `oneof`, so its fields are
# recognized by their `Request` suffix, which fields outside of it don't have.
_BATCH_CHANGE_TYPES = tuple(
    sorted(
        field.name
        for field in _BatchChange.all_fields()
        if field.name.endswith("Request")
    )
)


def IsoDateTime(datetime_str: str) -> str:
  """Parses datetime string, validates it and outputs the new datetime string in ISO format."""
  return arg_parsers.Datetime.Parse(datetime_str).isoformat()


def ParseAspects(
    aspects_file: str,
) -> dataplex_message.GoogleCloudDataplexV1Entry.AspectsValue:
  """Parse aspects from a YAML or JSON file.

  Perform a basic validation that aspects are provided in a correct format.

  Args:
    aspects_file: The path to the YAML/JSON file containing aspects.

  Returns:
    A list of aspects parsed to a proto message (AspectsValue).
  """
  parser = arg_parsers.YAMLFileContents()
  raw_aspects = parser(aspects_file)

  if not isinstance(raw_aspects, dict):
    raise arg_parsers.ArgumentTypeError(
        f"Invalid aspects file: {aspects_file}. It must contain a map with a"
        " key in the format `ASPECT_TYPE@PATH` (or just `ASPECT_TYPE` if"
        " attached to the root path). Values in the map represent Aspect's"
        " content, which must conform to a template defined for a given"
        " `ASPECT_TYPE`."
    )

  aspects = []
  for aspect_key, aspect in raw_aspects.items():
    aspects.append(
        dataplex_message.GoogleCloudDataplexV1Entry.AspectsValue.AdditionalProperty(
            key=aspect_key,
            value=messages_util.DictToMessageWithErrorCheck(
                aspect, dataplex_message.GoogleCloudDataplexV1Aspect
            ),
        )
    )
  return dataplex_message.GoogleCloudDataplexV1Entry.AspectsValue(
      additionalProperties=aspects
  )


def ParseEntryLinkAspects(
    aspects_file: str,
) -> dataplex_message.GoogleCloudDataplexV1EntryLink.AspectsValue:
  """Parse aspects from a YAML or JSON file for EntryLinks.

  Perform a basic validation that aspects are provided in a correct format.
  Aspect keys for EntryLinks cannot contain paths.

  Args:
    aspects_file: The path to the YAML/JSON file containing aspects.

  Returns:
    A list of aspects parsed to a proto message (AspectsValue).
  """
  parser = arg_parsers.YAMLFileContents()
  raw_aspects = parser(aspects_file)

  if not isinstance(raw_aspects, dict):
    raise arg_parsers.ArgumentTypeError(
        f"Invalid aspects file: {aspects_file}. It must contain a map with a"
        " key in the format `PROJECT_ID.LOCATION.ASPECT_TYPE_ID`. Values in the"
        " map represent Aspect's content, which must conform to a template"
        " defined for a given `PROJECT_ID.LOCATION.ASPECT_TYPE_ID`."
    )

  aspects = []
  for aspect_key, aspect in raw_aspects.items():
    if "@" in aspect_key:
      raise arg_parsers.ArgumentTypeError(
          f'Aspect key "{aspect_key}" is invalid for an EntryLink. Aspect keys'
          ' for EntryLinks must be in PROJECT_ID.LOCATION.ASPECT_TYPE_ID format'
          ' and cannot contain a path.'
      )
    aspects.append(
        dataplex_message.GoogleCloudDataplexV1EntryLink.AspectsValue.AdditionalProperty(
            key=aspect_key,
            value=messages_util.DictToMessageWithErrorCheck(
                aspect, dataplex_message.GoogleCloudDataplexV1Aspect
            ),
        )
    )
  return dataplex_message.GoogleCloudDataplexV1EntryLink.AspectsValue(
      additionalProperties=aspects
  )


def ParseEntrySourceAncestors(ancestors: List[str]):
  """Parse ancestors from a string.

  Args:
    ancestors: A list of strings containing the JSON representation of the
      Ancestors.

  Returns:
    A list of ancestors parsed to a proto message
    (GoogleCloudDataplexV1EntrySourceAncestor).
  """
  if ancestors is None:
    return []
  return list(
      map(
          lambda ancestor: messages_util.DictToMessageWithErrorCheck(
              json.loads(ancestor),
              dataplex_message.GoogleCloudDataplexV1EntrySourceAncestor,
          ),
          ancestors,
      )
  )


def ParseAccessGroups(access_groups):
  """Parse access groups from a list of JSON strings.

  Args:
    access_groups: A list of JSON strings representing Access Group(s).

  Returns:
    A list of AdditionalProperty objects.
  """
  if access_groups is None:
    return None

  items = []
  for access_group in access_groups:
    access_group_msg = messages_util.DictToMessageWithErrorCheck(
        dataplex_util.SnakeToCamelDict(json.loads(access_group)),
        dataplex_message.GoogleCloudDataplexV1DataProductAccessGroup,
    )

    if not access_group_msg.id:
      raise arg_parsers.ArgumentTypeError(
          'Access group must have an "id" field.'
      )

    items.append(
        dataplex_message.GoogleCloudDataplexV1DataProduct.AccessGroupsValue.AdditionalProperty(
            key=access_group_msg.id, value=access_group_msg
        )
    )
  return items


def ParseAccessGroupConfigs(access_group_configs):
  """Parse access group configs from a list of JSON strings.

  Args:
    access_group_configs: A list of JSON strings representing Access Group
      Config(s).

  Returns:
    A list of AdditionalProperty objects.
  """
  if access_group_configs is None:
    return None

  additional_properties = []
  for access_group_config in access_group_configs:
    config_dict = json.loads(access_group_config)

    group_id = config_dict.pop("id", None)
    if not group_id:
      raise arg_parsers.ArgumentTypeError(
          'Access group config must have an "id" field.'
      )

    access_group_config_msg = messages_util.DictToMessageWithErrorCheck(
        dataplex_util.SnakeToCamelDict(config_dict),
        dataplex_message.GoogleCloudDataplexV1DataAssetAccessGroupConfig,
    )

    additional_properties.append(
        dataplex_message.GoogleCloudDataplexV1DataAsset.AccessGroupConfigsValue.AdditionalProperty(
            key=group_id, value=access_group_config_msg
        )
    )

  return additional_properties


def ParseBatchChanges(
    changes_file: str,
) -> list[
    dataplex_message.GoogleCloudDataplexV1BatchChangeMetadataRequestChange
]:
  """Parses batch metadata changes from a YAML or JSON file.

  The file must contain a non-empty list of changes. Each change is a
  `BatchChangeMetadataRequest.Change` in its REST (camelCase) representation,
  with exactly one of `createEntryRequest`, `updateEntryRequest`,
  `deleteEntryRequest`, `createEntryLinkRequest`, `updateEntryLinkRequest` or
  `deleteEntryLinkRequest` set to an object. YAML timestamps and dates are
  converted to ISO 8601 strings.

  Args:
    changes_file: The path to the YAML or JSON file, or '-' to read the changes
      from stdin.

  Returns:
    The changes, in the order in which they appear in the file.

  Raises:
    calliope_exceptions.BadFileException: If the file cannot be read or does
      not contain a valid list of changes. For an invalid change, the message
      contains its 0-based position in the list, for example `changes[2]`.
  """
  raw_changes = _LoadJsonCompatibleYaml(changes_file)
  if not isinstance(raw_changes, list) or not raw_changes:
    raise calliope_exceptions.BadFileException(
        f"Invalid changes file [{changes_file}]: expected a non-empty list of"
        " changes."
    )
  return [
      _ParseBatchChange(changes_file, index, raw_change)
      for index, raw_change in enumerate(raw_changes)
  ]


def _LoadJsonCompatibleYaml(path: str) -> Any:
  """Loads a YAML or JSON file into values that can be represented as JSON.

  YAML parses unquoted timestamps and dates into `datetime` objects, but the
  API expects them as strings, so they are converted to ISO 8601 strings.

  Args:
    path: The path to the file, or '-' to read from stdin.

  Returns:
    The parsed contents of the file.

  Raises:
    calliope_exceptions.BadFileException: If the file cannot be read or parsed,
      or contains values that cannot be represented as JSON, such as cyclic
      aliases, binary data, or NaN and infinite numbers.
  """
  try:
    data = yaml.load(
        console_io.ReadFromFileOrStdin(path, binary=False), file_hint=path
    )
    return json.loads(
        json.dumps(data, default=_DateToIsoString, allow_nan=False)
    )
  except (files.Error, yaml.Error) as e:
    raise calliope_exceptions.BadFileException(str(e)) from e
  except (TypeError, ValueError) as e:  # ValueError includes UnicodeError.
    raise calliope_exceptions.BadFileException(
        f"Invalid changes file [{path}]: {e}"
    ) from e


def _DateToIsoString(value: Any) -> str:
  """Converts a YAML timestamp or date to an ISO 8601 string for json.dumps.

  Args:
    value: A value that `json.dumps` cannot serialize by itself.

  Returns:
    The ISO 8601 representation of the value.

  Raises:
    TypeError: If the value is neither a timestamp nor a date.
  """
  if isinstance(value, datetime.datetime):
    # YAML timestamps are in UTC, and the YAML parser returns them as naive
    # datetimes.
    return value.isoformat() + ("Z" if value.tzinfo is None else "")
  if isinstance(value, datetime.date):
    return value.isoformat()
  raise TypeError(f"Unsupported value of type [{type(value).__name__}].")


def _ParseBatchChange(
    changes_file: str, index: int, raw_change: Any
) -> _BatchChange:
  """Parses the change at the given position in the file.

  Args:
    changes_file: The path to the file, for error messages.
    index: The 0-based position of the change in the file.
    raw_change: The change as loaded from the file.

  Returns:
    The parsed change.

  Raises:
    calliope_exceptions.BadFileException: If the change is invalid.
  """
  change_types = (
      [key for key in _BATCH_CHANGE_TYPES if key in raw_change]
      if isinstance(raw_change, dict)
      else []
  )
  if len(change_types) != 1:
    expected_types = ", ".join(_BATCH_CHANGE_TYPES)
    raise _MakeInvalidChangeError(
        changes_file,
        index,
        f"expected a map with exactly one of [{expected_types}].",
    )
  change_type = change_types[0]
  payload = raw_change[change_type]
  if not isinstance(payload, dict):
    raise _MakeInvalidChangeError(
        changes_file, index, f"[{change_type}] must be an object."
    )
  # TODO(b/564890653): Revisit once the batch API supports validate_only.
  if "validateOnly" in payload:
    raise _MakeInvalidChangeError(
        changes_file,
        index,
        f"[{change_type}.validateOnly] is not supported in a batch, where the"
        " service would ignore it and apply the change.",
    )
  try:
    return messages_util.DictToMessageWithErrorCheck(raw_change, _BatchChange)
  except messages_util.DecodeError as e:
    raise _MakeInvalidChangeError(changes_file, index, str(e)) from e
  except AttributeError as e:
    # apitools raises AttributeError instead of DecodeError when a field that
    # expects an object has a value of another type.
    raise _MakeInvalidChangeError(
        changes_file,
        index,
        "a field that expects an object has a value of another type.",
    ) from e


def _MakeInvalidChangeError(
    changes_file: str, index: int, reason: str
) -> calliope_exceptions.BadFileException:
  """Returns the error for the invalid change at the given position."""
  return calliope_exceptions.BadFileException(
      f"Invalid change at changes[{index}] in [{changes_file}]: {reason}"
  )
