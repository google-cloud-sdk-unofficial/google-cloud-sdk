# -*- coding: utf-8 -*- # Lint as: python3
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
"""Type definitions for Apigee Feature Templates."""

import dataclasses
import re
import typing
from typing import Any, Dict, List, Optional, TypeVar, Union

T = TypeVar("T", bound=dataclasses.dataclass)


def _to_snake_case(name: str) -> str:
  """Converts a camelCase string to snake_case."""
  # This regex matches every position that satisfies both of these conditions:
  # - not at the beginning of the string (the lookbehind `(?<!^)`)
  # - immediately followed by an uppercase letter (the lookahead `(?=[A-Z])`)
  # The matches are zero-length, so replacing them with "_" effectively just
  # means "add an underscore there".
  return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def _to_camel_case(name: str) -> str:
  """Converts a snake_case string to camelCase."""
  parts = name.split("_")
  return parts[0] + "".join(x.capitalize() for x in parts[1:])


def from_dict(cls: type[T], data: dict[str, Any]) -> T:
  """Creates a dataclass instance from a dictionary."""
  field_types = {f.name: f.type for f in dataclasses.fields(cls)}
  rewritten_data = {}
  for k, v in data.items():
    # The dataclasses use snake_case to match Python conventions, but the
    # dictionary representation uses camelCase to match the YAML format.
    k = _to_snake_case(k)

    if k not in field_types:
      raise ValueError(
          f'{cls} objects do not have a field named "{k}": {data!r}'
      )
    field_type = field_types[k]
    origin_type = typing.get_origin(field_type)
    type_args = typing.get_args(field_type)

    # Make sure that nested dataclasses and lists of dataclasses are
    # converted from dicts to instances.
    if dataclasses.is_dataclass(field_type) and isinstance(v, dict):
      v = from_dict(field_type, v)
    elif origin_type and type_args:
      # Handle parameterized types: Optional, List, etc.
      # Optional[T] is represented as Union[T, None] under the hood, so checking
      # it requires matching the Union pattern instead of the Optional pattern.
      is_optional = (origin_type is Union
                     and type(None) in type_args
                     and len(type_args) == 2)

      # Determine the wrapped dataclass type, if any.
      dataclass_args = [t for t in type_args if dataclasses.is_dataclass(t)]
      inner_dataclass = dataclass_args[0] if dataclass_args else None

      if is_optional and inner_dataclass and v is not None:
        v = from_dict(inner_dataclass, v)
      elif origin_type is list and inner_dataclass:
        v = [e if dataclasses.is_dataclass(e) else from_dict(inner_dataclass, e)
             for e in v]
    rewritten_data[k] = v

  return cls(**rewritten_data)


def _snake_to_camel_dict_factory(
    data: list[tuple[str, Any]],
) -> dict[str, Any]:
  """Build a dict with camelCase keys from a list of (snake_case, value) tuples."""
  return {
      _to_camel_case(k): v
      for k, v in data
  }


def to_dict(instance: T) -> dict[str, Any]:
  """Converts a dataclass instance to a dictionary."""
  return dataclasses.asdict(instance, dict_factory=_snake_to_camel_dict_factory)


class AftSchemaError(ValueError):
  """Raised when an AFT document violates the schema contract."""


# Closed supported sets for the top-level discriminator fields. Both are sorted
# in error messages for deterministic, parity-friendly diagnostics.
SUPPORTED_GATEWAYS = frozenset({"apigee"})
SUPPORTED_SCHEMA_VERSIONS = frozenset({"1.0.0"})


def _validate_supported_field(
    field_name: str, value: str, supported_values: frozenset[str]
) -> None:
  if not value:
    raise AftSchemaError(f"missing required top-level {field_name!r} field")
  if value not in supported_values:
    supported = ", ".join(sorted(supported_values))
    raise AftSchemaError(
        f"unsupported {field_name} {value!r}; supported: {supported}"
    )


def validate_gateway(value: str) -> None:
  """Validates the top-level `gateway` field (missing-first, then unsupported).

  Args:
    value: The gateway value to validate.

  Raises:
    AftSchemaError: If `value` is empty/missing or not a supported gateway.
  """
  _validate_supported_field("gateway", value, SUPPORTED_GATEWAYS)


def validate_schema_version(value: str) -> None:
  """Validates the top-level `schemaVersion` field (missing-first, then unsupported).

  Args:
    value: The schemaVersion value to validate.

  Raises:
    AftSchemaError: If `value` is empty/missing or not a supported version.
  """
  _validate_supported_field("schemaVersion", value, SUPPORTED_SCHEMA_VERSIONS)


@dataclasses.dataclass
class Parameter:
  name: str = ""
  paths: Optional[List[str]] = None
  display_name: str = ""
  description: str = ""
  maps: Optional[Dict[str, str]] = None
  examples: List[str] = dataclasses.field(default_factory=list)
  default: str = ""


@dataclasses.dataclass
class Route:
  name: str = ""
  condition: Optional[str] = None
  target: Optional[str] = None


@dataclasses.dataclass
class Step:
  name: str = ""
  condition: Optional[str] = None


@dataclasses.dataclass
class Flow:
  name: str
  mode: Optional[str] = None
  condition: Optional[str] = None
  steps: List[Step] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class FaultRule(Flow):
  always_enforce: bool = False


@dataclasses.dataclass
class Endpoint:
  name: str = ""
  base_path: str = ""
  routes: List[Route] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class ProxyEndpoint(Endpoint):
  flows: List[Flow] = dataclasses.field(default_factory=list)
  post_client_flow: Optional[Flow] = None
  fault_rules: List[Flow] = dataclasses.field(default_factory=list)
  default_fault_rule: Optional[FaultRule] = None


@dataclasses.dataclass
class Target:
  name: str = ""
  url: str = ""
  auth: Optional[str] = None
  scopes: List[str] = dataclasses.field(default_factory=list)
  aud: Optional[str] = None


@dataclasses.dataclass
class ProxyTarget(Target):
  flows: List[Flow] = dataclasses.field(default_factory=list)
  fault_rules: List[Flow] = dataclasses.field(default_factory=list)
  default_fault_rule: Optional[FaultRule] = None
  http_target_connection: Optional[Dict[str, Any]] = None
  local_target_connection: Optional[Dict[str, Any]] = None


@dataclasses.dataclass
class Policy:
  name: str = ""
  type: str = ""
  content: Dict[str, Any] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class Resource:
  """Represents a resource file to be included in an Apigee API proxy bundle."""

  name: str = ""
  type: str = ""
  content: str = ""


@dataclasses.dataclass
class Test:
  """Represents an Apigee API proxy test. Not yet implemented."""
  name: str = ""
  description: Optional[str] = None
  url: str = ""
  path: Optional[str] = None
  method: Optional[str] = None
  headers: List[str] = dataclasses.field(default_factory=list)
  request: Optional[str] = None
  query_params: List[str] = dataclasses.field(default_factory=list)
  variables: List[str] = dataclasses.field(default_factory=list)
  assertions: List[str] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class Template:
  """Represents an Apigee API proxy template."""

  gateway: str = ""
  schema_version: str = ""
  name: str = ""
  type: str = "template"
  priority: Optional[int] = None
  description: str = ""
  features: List[str] = dataclasses.field(default_factory=list)
  parameters: List[Parameter] = dataclasses.field(default_factory=list)
  endpoints: List[Endpoint] = dataclasses.field(default_factory=list)
  targets: List[Target] = dataclasses.field(default_factory=list)
  tests: List[Test] = dataclasses.field(default_factory=list)

  def __post_init__(self):
    validate_gateway(self.gateway)
    validate_schema_version(self.schema_version)


@dataclasses.dataclass
class Proxy:
  """Represents an Apigee API proxy."""

  gateway: str = ""
  schema_version: str = ""
  name: str = ""
  display_name: Optional[str] = None
  uid: Optional[str] = None
  type: str = "proxy"
  priority: Optional[int] = None
  categories: List[str] = dataclasses.field(default_factory=list)
  description: str = ""
  documentation: Optional[str] = None
  parameters: List[Parameter] = dataclasses.field(default_factory=list)
  endpoints: List[ProxyEndpoint] = dataclasses.field(default_factory=list)
  targets: List[ProxyTarget] = dataclasses.field(default_factory=list)
  policies: List[Policy] = dataclasses.field(default_factory=list)
  resources: List[Resource] = dataclasses.field(default_factory=list)
  tests: List[Test] = dataclasses.field(default_factory=list)

  def __post_init__(self):
    validate_gateway(self.gateway)
    validate_schema_version(self.schema_version)


@dataclasses.dataclass
class Feature:
  """Represents an abstract feature to be included in a templated Apigee proxy."""

  gateway: str = ""
  schema_version: str = ""
  name: str = ""
  display_name: Optional[str] = None
  uid: Optional[str] = None
  type: str = "feature"
  description: str = ""
  documentation: Optional[str] = None
  priority: Optional[int] = None
  categories: List[str] = dataclasses.field(default_factory=list)
  parameters: List[Parameter] = dataclasses.field(default_factory=list)
  default_endpoint: Optional[ProxyEndpoint] = None
  default_target: Optional[ProxyTarget] = None
  endpoints: List[ProxyEndpoint] = dataclasses.field(default_factory=list)
  targets: List[ProxyTarget] = dataclasses.field(default_factory=list)
  policies: List[Policy] = dataclasses.field(default_factory=list)
  resources: List[Resource] = dataclasses.field(default_factory=list)
  tests: List[Test] = dataclasses.field(default_factory=list)

  def __post_init__(self):
    validate_gateway(self.gateway)
    validate_schema_version(self.schema_version)
