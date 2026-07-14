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
from typing import Any, Dict, List, Optional, TypeVar

T = TypeVar("T", bound=dataclasses.dataclass)


def _to_snake_case(name: str) -> str:
  """Converts a camelCase string to snake_case."""
  return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def _to_camel_case(name: str) -> str:
  """Converts a snake_case string to camelCase."""
  parts = name.split("_")
  return parts[0] + "".join(x.capitalize() for x in parts[1:])


def from_dict(cls: type[T], data: dict[str, Any]) -> T:
  """Creates a dataclass instance from a dictionary."""
  # Dictionary representation uses camelCase, while dataclasses use
  # snake_case.

  snakey_data = {}
  for k, v in data.items():
    snakey_data[_to_snake_case(k)] = v

  return cls(
      **{
          k: v
          for k, v in data.items()
          if k in dataclasses.fields(cls)
      }
  )


def to_dict(instance: T) -> dict[str, Any]:
  """Converts a dataclass instance to a dictionary."""
  data = dataclasses.asdict(instance)
  return {
      _to_camel_case(k): v
      for k, v in data.items()
      if k in dataclasses.fields(instance) and v is not None
  }


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

  name: str = ""
  type: str = "template"
  priority: Optional[int] = None
  description: str = ""
  features: List[str] = dataclasses.field(default_factory=list)
  parameters: List[Parameter] = dataclasses.field(default_factory=list)
  endpoints: List[Endpoint] = dataclasses.field(default_factory=list)
  targets: List[Target] = dataclasses.field(default_factory=list)
  tests: List[Test] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class Proxy:
  """Represents an Apigee API proxy."""

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


@dataclasses.dataclass
class Feature:
  """Represents an abstract feature to be included in a templated Apigee proxy."""

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
